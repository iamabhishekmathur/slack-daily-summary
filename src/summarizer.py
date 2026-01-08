"""AI-powered summarization using OpenAI"""

import logging
import time
from typing import Dict, List, Any
from openai import OpenAI
from openai import RateLimitError, APIError
from src.config import Config

logger = logging.getLogger(__name__)


class Summarizer:
    """Generate AI summaries of Slack conversations using OpenAI"""

    SYSTEM_PROMPT = """You are a helpful assistant that summarizes Slack messages concisely.
Create brief, actionable summaries that highlight:
1. Key decisions or action items
2. Important questions that need responses
3. Critical updates or announcements
4. Relevant discussions by topic

Format: Brief overview (1-2 sentences) followed by bullet points for key details.
Be direct and skip pleasantries. Focus on what matters."""

    def __init__(self, api_key: str, model: str = None):
        """
        Initialize summarizer

        Args:
            api_key: OpenAI API key
            model: Model to use (default from config)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model or Config.OPENAI_MODEL
        logger.info(f"Summarizer initialized with model: {self.model}")

    def summarize_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate summaries for all conversations

        Args:
            conversations: List of processed conversations from MessageProcessor

        Returns:
            List of conversations with added 'summary' field
        """
        if not conversations:
            logger.info("No conversations to summarize")
            return []

        logger.info(f"Summarizing {len(conversations)} conversations...")

        summarized = []
        for conv in conversations:
            try:
                summary = self._summarize_conversation(conv)
                conv['summary'] = summary
                summarized.append(conv)
                logger.debug(f"Summarized {conv['channel_name']}")
            except Exception as e:
                logger.error(f"Error summarizing {conv['channel_name']}: {e}")
                # Add fallback summary
                conv['summary'] = self._create_fallback_summary(conv)
                summarized.append(conv)

        logger.info(f"Completed summarization of {len(summarized)} conversations")
        return summarized

    def _summarize_conversation(self, conversation: Dict[str, Any]) -> str:
        """
        Generate summary for a single conversation

        Args:
            conversation: Processed conversation dict

        Returns:
            Summary text
        """
        # Create prompt
        prompt = self._create_prompt(conversation)

        # Call OpenAI API with retry logic
        summary = self._call_openai_api(prompt)

        return summary

    def _create_prompt(self, conversation: Dict[str, Any]) -> str:
        """
        Create prompt for OpenAI

        Args:
            conversation: Processed conversation dict

        Returns:
            Formatted prompt string
        """
        channel_name = conversation['channel_name']
        messages = conversation['messages']
        threads = conversation['threads']
        total_count = conversation['total_count']

        # Build message list
        message_lines = []

        # Add regular messages
        for msg in messages:
            timestamp = msg['timestamp']
            user = msg['user_name']
            text = msg['text']
            message_lines.append(f"- [{timestamp}] {user}: {text}")

        # Add threads
        for thread in threads:
            parent = thread['parent']
            replies = thread['replies']

            # Add parent
            message_lines.append(f"\n[THREAD] {parent['user_name']}: {parent['text']}")

            # Add replies
            for reply in replies:
                message_lines.append(f"  └─ {reply['user_name']}: {reply['text']}")

            # Note if there are more replies
            if thread['reply_count'] > thread['showing_count']:
                remaining = thread['reply_count'] - thread['showing_count']
                message_lines.append(f"  └─ ... and {remaining} more replies")

        messages_text = "\n".join(message_lines)

        # Build prompt
        prompt = f"""Summarize these unread Slack messages from {channel_name}:

{messages_text}

Total messages: {total_count}

Provide a brief summary with key points."""

        return prompt

    def _call_openai_api(self, prompt: str) -> str:
        """
        Call OpenAI API with retry logic

        Args:
            prompt: User prompt

        Returns:
            Generated summary
        """
        retries = 0
        backoff = 1

        while retries < Config.MAX_RETRIES:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=Config.MAX_TOKENS_OUTPUT,
                    temperature=0.3  # Lower temperature for more focused summaries
                )

                summary = response.choices[0].message.content.strip()
                return summary

            except RateLimitError as e:
                retries += 1
                if retries < Config.MAX_RETRIES:
                    wait_time = backoff * Config.BACKOFF_FACTOR
                    logger.warning(f"Rate limited by OpenAI. Waiting {wait_time}s before retry {retries}/{Config.MAX_RETRIES}")
                    time.sleep(wait_time)
                    backoff *= Config.BACKOFF_FACTOR
                else:
                    raise Exception(f"Max retries ({Config.MAX_RETRIES}) exceeded for OpenAI rate limiting") from e

            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                raise

        raise Exception("Failed to get summary from OpenAI")

    def _create_fallback_summary(self, conversation: Dict[str, Any]) -> str:
        """
        Create a fallback summary if AI summarization fails

        Args:
            conversation: Processed conversation dict

        Returns:
            Fallback summary text
        """
        count = conversation['total_count']
        channel_name = conversation['channel_name']

        # Extract first few message snippets
        snippets = []
        for msg in conversation['messages'][:3]:
            text = msg['text'][:100]
            snippets.append(f"• {msg['user_name']}: {text}...")

        for thread in conversation['threads'][:2]:
            parent = thread['parent']
            text = parent['text'][:100]
            reply_count = thread['reply_count']
            snippets.append(f"• [Thread] {parent['user_name']}: {text}... ({reply_count} replies)")

        snippet_text = "\n".join(snippets) if snippets else "No message preview available."

        return f"""**{count} unread messages in {channel_name}**

{snippet_text}

(AI summary unavailable - showing message preview)"""
