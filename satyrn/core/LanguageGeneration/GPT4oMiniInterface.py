'''
This file is part of Satyrn.
Satyrn is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.
Satyrn is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with Satyrn.
If not, see <https://www.gnu.org/licenses/>.
'''

import os
import httpx
from openai import APITimeoutError, APIConnectionError, OpenAI

from typing import Dict

class GPT4oMiniInterface:
    def __init__(self):
        # Init access to OpenAI's API
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        timeout_seconds = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "60"))
        max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", "2"))
        self.client = OpenAI(
            api_key=self.openai_api_key,
            timeout=httpx.Timeout(timeout_seconds, connect=10.0, write=20.0, read=timeout_seconds),
            max_retries=max_retries,
        )

    def generate(self,
                 prompt: str,
                 temp: float = 0.0,
                 max_tokens: int = 1024,
                 response_format_type: str = 'text') -> str:
        # Feed the prompt to the language model
        response = self.get_response(prompt,
                                     temp=temp,
                                     max_tokens=max_tokens,
                                     response_format_type=response_format_type)

        # Extract the generation from the response
        qdmr = self.extract_generation_from_response(response)

        return qdmr

    def get_response(self,
                     prompt: str,
                     temp: float = 0.0,
                     max_tokens: int = 1024,
                     response_format_type: str = 'text') -> Dict:
        # Make the API call off to GPT
        print(f"Prompt:\n{prompt}")
        try:
            response = self.client.chat.completions.create(
                # model="gpt-4o-mini",
                # slightly cheaper model
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temp,
                response_format={"type": response_format_type},
            )
        except APITimeoutError as exc:
            raise RuntimeError(
                "OpenAI request timed out. "
                "Consider reducing prompt size or increasing OPENAI_TIMEOUT_SECONDS."
            ) from exc
        except APIConnectionError as exc:
            raise RuntimeError(
                "OpenAI request failed due to a network connection issue."
            ) from exc

        # Save the raw output
        print("RAW OPENAI RESPONSE")
        print(response)

        return response

    def extract_generation_from_response(self,
                                   response: Dict) -> str:
        # Pull out the generated text from the response
        message_content = response.choices[0].message.content

        # Clean up the string
        message_content = message_content.strip()

        return message_content
