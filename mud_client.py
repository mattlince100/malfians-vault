"""MUD client for connecting and communicating with Realms of Despair."""

import asyncio
import telnetlib3
import time
import logging
from typing import Optional, Tuple

# Suppress telnet protocol negotiation warnings to reduce log spam
logging.getLogger('telnetlib3.stream_writer').setLevel(logging.ERROR)
from config import (
    MUD_HOST, MUD_PORT, CONNECTION_TIMEOUT, 
    COMMAND_DELAY, LOGIN_DELAY, DEBUG_MODE
)

logger = logging.getLogger(__name__)


class MUDClient:
    """Handles telnet connection and communication with the MUD."""
    
    def __init__(self):
        self.reader: Optional[telnetlib3.TelnetReader] = None
        self.writer: Optional[telnetlib3.TelnetWriter] = None
        self.connected = False
        self.buffer = []
        
    async def connect(self) -> bool:
        """Establish telnet connection to the MUD."""
        try:
            logger.info(f"Connecting to {MUD_HOST}:{MUD_PORT}")
            self.reader, self.writer = await asyncio.wait_for(
                telnetlib3.open_connection(MUD_HOST, MUD_PORT),
                timeout=CONNECTION_TIMEOUT
            )
            self.connected = True
            logger.info("Connected successfully")
            
            # Clear initial connection messages
            await asyncio.sleep(2)
            initial_response = await self._read_until_prompt()
            logger.debug(f"Initial connection response: '{initial_response}'")
            
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {MUD_HOST}:{MUD_PORT}")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return False
    
    async def login(self, username: str, password: str) -> bool:
        """Login to the MUD with character credentials."""
        if not self.connected:
            logger.error("Not connected to MUD")
            return False
            
        try:
            logger.info(f"Logging in as {username}")
            
            # Send username
            self.writer.write(username + '\n')
            await self.writer.drain()
            await asyncio.sleep(1)
            
            # Wait for password prompt
            response = await self._read_until_prompt()
            logger.debug(f"After username: '{response}'")
            
            # Send password
            self.writer.write(password + '\n')
            await self.writer.drain()
            await asyncio.sleep(LOGIN_DELAY)
            
            # Check for successful login
            response = await self._read_until_prompt()
            logger.debug(f"After password: '{response}'")
            
            # Check if we need to press Enter to continue
            if "press enter" in response.lower() or "[press enter]" in response.lower():
                logger.debug("MUD requires pressing Enter to continue")
                # Press Enter twice as MUDs often require this
                self.writer.write('\n')
                await self.writer.drain()
                await asyncio.sleep(1)
                
                self.writer.write('\n')
                await self.writer.drain()
                await asyncio.sleep(2)
                
                # Read the next response
                response = await self._read_until_prompt()
                logger.debug(f"After pressing Enter twice: '{response}'")
                
            # Look for signs of successful login
            if ("welcome" in response.lower() or 
                username.lower() in response.lower() or
                "last connected" in response.lower() or
                "press enter" in response.lower()):
                logger.info(f"Successfully logged in as {username}")
                
                # Disable ANSI colors for cleaner parsing
                logger.debug("Disabling ANSI colors with 'config -ansi'")
                await self.send_command("config -ansi", delay=1)
                
                return True
            else:
                logger.error(f"Login failed for {username}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    async def send_command(self, command: str, delay: float = None) -> str:
        """Send a command to the MUD and return the response."""
        if not self.connected:
            logger.error("Not connected to MUD")
            return ""
            
        try:
            if delay is None:
                delay = COMMAND_DELAY
                
            logger.debug(f"Sending command: {command}")
            
            # Clear buffer
            self.buffer = []
            
            # Send command
            self.writer.write(command + '\n')
            await self.writer.drain()
            
            # Wait for response
            await asyncio.sleep(delay)
            
            # Read response
            response = await self._read_until_prompt()
            
            if DEBUG_MODE:
                logger.debug(f"Response: {response[:200]}...")
                
            return response
            
        except Exception as e:
            logger.error(f"Command error: {str(e)}")
            return ""
    
    async def logout(self) -> bool:
        """Logout from the MUD cleanly."""
        try:
            logger.info("Logging out")
            
            # Re-enable ANSI colors before logout
            logger.debug("Re-enabling ANSI colors with 'config +ansi'")
            await self.send_command("config +ansi", delay=0.5)
            
            await self.send_command("quit", delay=1)
            return True
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    async def disconnect(self):
        """Close the telnet connection."""
        try:
            if self.writer:
                self.writer.close()
                # telnetlib3's writer doesn't have wait_closed(), just close() is sufficient
            self.connected = False
            logger.info("Disconnected")
        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")
    
    async def _read_until_prompt(self, timeout: float = 1.5) -> str:
        """Read data until we detect a prompt or timeout."""
        data = ""
        start_time = time.time()
        last_data_time = start_time
        
        while time.time() - start_time < timeout:
            try:
                # Read available data
                chunk = await asyncio.wait_for(
                    self.reader.read(1024),
                    timeout=0.2
                )
                if chunk:
                    # telnetlib3 returns strings, not bytes
                    if isinstance(chunk, bytes):
                        text = chunk.decode('utf-8', errors='ignore')
                    else:
                        text = chunk
                    text = self._strip_ansi(text)
                    data += text
                    last_data_time = time.time()
                    
                    # Check for common prompts (but not equipment slots)
                    if any(prompt in data.lower() for prompt in [
                        'hp:', 'password:', 'continue', 'press return'
                    ]):
                        break
                        
                else:
                    # No data received, check if we should timeout
                    if time.time() - last_data_time > 0.8:
                        # No new data for 0.8 seconds, likely done
                        break
                        
            except asyncio.TimeoutError:
                # No data available, check for completion
                if time.time() - last_data_time > 0.8:
                    # No new data for 0.8 seconds, likely done
                    break
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.debug(f"Read error: {str(e)}")
                break
                
        return data
    
    @staticmethod
    def _strip_ansi(text: str) -> str:
        """Remove ANSI escape codes from text."""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)