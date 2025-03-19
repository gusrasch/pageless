#!/usr/bin/env python3
import os
import sys
import json
from typing import Dict, Any, Optional, List
import httpx
from mcp.server.fastmcp import FastMCP

# Check for required environment variables
bot_token = os.environ.get("SLACK_BOT_TOKEN")
team_id = os.environ.get("SLACK_TEAM_ID")

if not bot_token or not team_id:
    print("Please set SLACK_BOT_TOKEN and SLACK_TEAM_ID environment variables", file=sys.stderr)
    sys.exit(1)

print("Starting Slack MCP Server...", file=sys.stderr)

# Initialize FastMCP server
mcp = FastMCP("Slack MCP Server")

class SlackClient:
    def __init__(self, bot_token: str):
        self.bot_headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
    
    async def get_channels(self, limit: int = 100, cursor: Optional[str] = None) -> Dict[str, Any]:
        """List public channels in the workspace with pagination"""
        params = {
            "types": "public_channel",
            "exclude_archived": "true",
            "limit": str(min(limit, 200)),
            "team_id": team_id
        }
        
        if cursor:
            params["cursor"] = cursor
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://slack.com/api/conversations.list",
                headers=self.bot_headers,
                params=params
            )
            return response.json()
    
    async def post_message(self, channel_id: str, text: str) -> Dict[str, Any]:
        """Post a new message to a Slack channel"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers=self.bot_headers,
                json={
                    "channel": channel_id,
                    "text": text
                }
            )
            return response.json()
    
    async def post_reply(self, channel_id: str, thread_ts: str, text: str) -> Dict[str, Any]:
        """Reply to a specific message thread in Slack"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers=self.bot_headers,
                json={
                    "channel": channel_id,
                    "thread_ts": thread_ts,
                    "text": text
                }
            )
            return response.json()
    
    async def add_reaction(self, channel_id: str, timestamp: str, reaction: str) -> Dict[str, Any]:
        """Add a reaction emoji to a message"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/reactions.add",
                headers=self.bot_headers,
                json={
                    "channel": channel_id,
                    "timestamp": timestamp,
                    "name": reaction
                }
            )
            return response.json()
    
    async def get_channel_history(self, channel_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent messages from a channel"""
        params = {
            "channel": channel_id,
            "limit": str(limit)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://slack.com/api/conversations.history",
                headers=self.bot_headers,
                params=params
            )
            return response.json()
    
    async def get_thread_replies(self, channel_id: str, thread_ts: str) -> Dict[str, Any]:
        """Get all replies in a message thread"""
        params = {
            "channel": channel_id,
            "ts": thread_ts
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://slack.com/api/conversations.replies",
                headers=self.bot_headers,
                params=params
            )
            return response.json()
    
    async def get_users(self, limit: int = 100, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Get a list of all users in the workspace"""
        params = {
            "limit": str(min(limit, 200)),
            "team_id": team_id
        }
        
        if cursor:
            params["cursor"] = cursor
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://slack.com/api/users.list",
                headers=self.bot_headers,
                params=params
            )
            return response.json()
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get detailed profile information for a specific user"""
        params = {
            "user": user_id,
            "include_labels": "true"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://slack.com/api/users.profile.get",
                headers=self.bot_headers,
                params=params
            )
            return response.json()

# Initialize Slack client
slack_client = SlackClient(bot_token)

@mcp.tool()
async def slack_list_channels(limit: int = 100, cursor: Optional[str] = None) -> str:
    """List public channels in the workspace with pagination
    
    Args:
        limit: Maximum number of channels to return (default 100, max 200)
        cursor: Pagination cursor for next page of results
    """
    try:
        response = await slack_client.get_channels(limit, cursor)
        return json.dumps(response)
    except Exception as e:
        error_response = {"error": str(e)}
        return json.dumps(error_response)

@mcp.tool()
async def slack_post_message(channel_id: str, text: str) -> str:
    """Post a new message to a Slack channel
    
    Args:
        channel_id: The ID of the channel to post to
        text: The message text to post
    """
    try:
        if not channel_id or not text:
            raise ValueError("Missing required arguments: channel_id and text")
        
        response = await slack_client.post_message(channel_id, text)
        return json.dumps(response)
    except Exception as e:
        error_response = {"error": str(e)}
        return json.dumps(error_response)

@mcp.tool()
async def slack_reply_to_thread(channel_id: str, thread_ts: str, text: str) -> str:
    """Reply to a specific message thread in Slack
    
    Args:
        channel_id: The ID of the channel containing the thread
        thread_ts: The timestamp of the parent message in the format '1234567890.123456'
        text: The reply text
    """
    try:
        if not channel_id or not thread_ts or not text:
            raise ValueError("Missing required arguments: channel_id, thread_ts, and text")
        
        response = await slack_client.post_reply(channel_id, thread_ts, text)
        return json.dumps(response)
    except Exception as e:
        error_response = {"error": str(e)}
        return json.dumps(error_response)

@mcp.tool()
async def slack_add_reaction(channel_id: str, timestamp: str, reaction: str) -> str:
    """Add a reaction emoji to a message
    
    Args:
        channel_id: The ID of the channel containing the message
        timestamp: The timestamp of the message to react to
        reaction: The name of the emoji reaction (without ::)
    """
    try:
        if not channel_id or not timestamp or not reaction:
            raise ValueError("Missing required arguments: channel_id, timestamp, and reaction")
        
        response = await slack_client.add_reaction(channel_id, timestamp, reaction)
        return json.dumps(response)
    except Exception as e:
        error_response = {"error": str(e)}
        return json.dumps(error_response)

@mcp.tool()
async def slack_get_channel_history(channel_id: str, limit: int = 10) -> str:
    """Get recent messages from a channel
    
    Args:
        channel_id: The ID of the channel
        limit: Number of messages to retrieve (default 10)
    """
    try:
        if not channel_id:
            raise ValueError("Missing required argument: channel_id")
        
        response = await slack_client.get_channel_history(channel_id, limit)
        return json.dumps(response)
    except Exception as e:
        error_response = {"error": str(e)}
        return json.dumps(error_response)

@mcp.tool()
async def slack_get_thread_replies(channel_id: str, thread_ts: str) -> str:
    """Get all replies in a message thread
    
    Args:
        channel_id: The ID of the channel containing the thread
        thread_ts: The timestamp of the parent message
    """
    try:
        if not channel_id or not thread_ts:
            raise ValueError("Missing required arguments: channel_id and thread_ts")
        
        response = await slack_client.get_thread_replies(channel_id, thread_ts)
        return json.dumps(response)
    except Exception as e:
        error_response = {"error": str(e)}
        return json.dumps(error_response)

@mcp.tool()
async def slack_get_users(limit: int = 100, cursor: Optional[str] = None) -> str:
    """Get a list of all users in the workspace with their basic profile information
    
    Args:
        limit: Maximum number of users to return (default 100, max 200)
        cursor: Pagination cursor for next page of results
    """
    try:
        response = await slack_client.get_users(limit, cursor)
        return json.dumps(response)
    except Exception as e:
        error_response = {"error": str(e)}
        return json.dumps(error_response)

@mcp.tool()
async def slack_get_user_profile(user_id: str) -> str:
    """Get detailed profile information for a specific user
    
    Args:
        user_id: The ID of the user
    """
    try:
        if not user_id:
            raise ValueError("Missing required argument: user_id")
        
        response = await slack_client.get_user_profile(user_id)
        return json.dumps(response)
    except Exception as e:
        error_response = {"error": str(e)}
        return json.dumps(error_response)

if __name__ == "__main__":
    try:
        # Run the server with stdio transport
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
