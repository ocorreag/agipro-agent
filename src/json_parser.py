import json
import re
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
import time

class PostData(BaseModel):
    """Validated post data structure"""
    fecha: str = Field(..., description="Date in YYYY-MM-DD format")
    titulo: str = Field(..., min_length=5, max_length=200, description="Post title")
    imagen: str = Field(..., min_length=10, description="Detailed image description")
    descripcion: str = Field(..., min_length=20, description="Post content with hashtags")

    @validator('fecha')
    def validate_date_format(cls, v):
        import datetime
        try:
            datetime.datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    @validator('titulo')
    def validate_titulo(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('imagen')
    def validate_imagen(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Image description cannot be empty')
        return v.strip()

    @validator('descripcion')
    def validate_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Content description cannot be empty')
        return v.strip()

class PostsResponse(BaseModel):
    """Container for multiple posts"""
    posts: List[PostData] = Field(..., min_items=1, max_items=10)
    generation_info: Optional[Dict[str, Any]] = Field(default=None)

class JSONResponseParser:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def extract_json_from_response(self, response_text: str) -> Optional[str]:
        """Extract JSON from LLM response using multiple strategies"""

        # Strategy 1: Look for JSON blocks with markers
        json_block_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'<json>(.*?)</json>',
            r'JSON:\s*(\{.*?\})',
        ]

        for pattern in json_block_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # Strategy 2: Look for JSON-like structure starting with { and ending with }
        # Find the first { and last }
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')

        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            potential_json = response_text[start_idx:end_idx + 1]

            # Basic validation - count braces
            open_braces = potential_json.count('{')
            close_braces = potential_json.count('}')

            if open_braces == close_braces:
                return potential_json.strip()

        # Strategy 3: Look for array format
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']')

        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            potential_json = response_text[start_idx:end_idx + 1]
            return potential_json.strip()

        return None

    def clean_json_string(self, json_str: str) -> str:
        """Clean and fix common JSON formatting issues"""

        # Remove common problematic characters (but preserve newlines and tabs)
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)  # Remove control characters except \n and \t

        # Fix trailing commas (before } or ])
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Fix multiple consecutive whitespaces
        json_str = re.sub(r'\s+', ' ', json_str)

        return json_str.strip()

    def parse_json_with_retry(self, response_text: str, expected_posts: int = None) -> Optional[PostsResponse]:
        """Parse JSON response with multiple retry strategies"""

        print(f"\n=== Parsing JSON Response ===")
        print(f"Response length: {len(response_text)} characters")
        print(f"First 200 chars: {response_text[:200]}...")
        print(f"Last 200 chars: ...{response_text[-200:]}")

        # Extract JSON
        json_str = self.extract_json_from_response(response_text)
        if not json_str:
            print("❌ No JSON found in response")
            return None

        print(f"✓ Extracted JSON ({len(json_str)} chars)")

        for attempt in range(self.max_retries):
            try:
                # Clean the JSON string
                cleaned_json = self.clean_json_string(json_str)

                # Try to parse
                parsed_data = json.loads(cleaned_json)
                print(f"✓ JSON parsed successfully (attempt {attempt + 1})")

                # Handle different response formats
                if isinstance(parsed_data, list):
                    # Direct list of posts
                    posts_data = parsed_data
                elif isinstance(parsed_data, dict):
                    if 'posts' in parsed_data:
                        # Wrapped format: {"posts": [...]}
                        posts_data = parsed_data['posts']
                    else:
                        # Single post as dict, convert to list
                        posts_data = [parsed_data]
                else:
                    raise ValueError("Unexpected JSON structure")

                # Validate and create PostsResponse
                validated_posts = []
                for i, post_data in enumerate(posts_data):
                    try:
                        validated_post = PostData(**post_data)
                        validated_posts.append(validated_post)
                        print(f"✓ Post {i+1} validated: {validated_post.titulo[:50]}...")
                    except Exception as e:
                        print(f"❌ Post {i+1} validation failed: {e}")
                        continue

                if not validated_posts:
                    raise ValueError("No valid posts found after validation")

                response = PostsResponse(
                    posts=validated_posts,
                    generation_info={
                        "total_posts": len(validated_posts),
                        "parsing_attempts": attempt + 1
                    }
                )

                print(f"✅ Successfully parsed {len(validated_posts)} posts")
                return response

            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    # Try some basic repairs
                    json_str = self._attempt_json_repair(json_str)
                    time.sleep(self.retry_delay)
                    continue

            except Exception as e:
                print(f"❌ Validation failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue

        print(f"❌ Failed to parse after {self.max_retries} attempts")
        return None

    def _attempt_json_repair(self, json_str: str) -> str:
        """Attempt basic JSON repairs"""

        # Try to fix unescaped quotes more aggressively
        # Split by lines and fix line by line
        lines = json_str.split('\n')
        fixed_lines = []

        for line in lines:
            # Fix lines that look like: "key": "value with "quotes" inside"
            # This is a simplified approach
            if '":' in line and line.count('"') > 2:
                # Find the key part
                key_end = line.find('":')
                if key_end != -1:
                    key_part = line[:key_end + 2]  # Include ":
                    value_part = line[key_end + 2:].strip()

                    # If value starts and ends with quotes, fix internal quotes
                    if value_part.startswith('"') and value_part.endswith('"'):
                        value_content = value_part[1:-1]  # Remove surrounding quotes
                        # Escape internal quotes
                        value_content = value_content.replace('"', '\\"')
                        fixed_line = key_part + ' "' + value_content + '"'
                        fixed_lines.append(fixed_line)
                        continue

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def convert_to_csv_format(self, posts_response: PostsResponse) -> List[Dict[str, str]]:
        """Convert validated posts to CSV-compatible format"""
        csv_posts = []

        for post in posts_response.posts:
            csv_posts.append({
                'fecha': post.fecha,
                'titulo': post.titulo,
                'imagen': post.imagen,
                'descripcion': post.descripcion
            })

        return csv_posts

# Convenience function for easy usage
def parse_posts_from_llm_response(response_text: str, expected_posts: int = None) -> Optional[List[Dict[str, str]]]:
    """Parse posts from LLM response and return CSV-compatible format"""
    parser = JSONResponseParser()
    posts_response = parser.parse_json_with_retry(response_text, expected_posts)

    if posts_response:
        return parser.convert_to_csv_format(posts_response)

    return None