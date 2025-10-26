#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "elevenlabs",
#     "python-dotenv",
# ]
# ///

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    """
    ElevenLabs Turbo v2.5 TTS Script
    
    Uses ElevenLabs' Turbo v2.5 model for fast, high-quality text-to-speech.
    Accepts optional text prompt as command-line argument.
    
    Usage:
    - ./eleven_turbo_tts.py                    # Uses default text
    - ./eleven_turbo_tts.py "Your custom text" # Uses provided text
    
    Features:
    - Fast generation (optimized for real-time use)
    - High-quality voice synthesis
    - Stable production model
    - Cost-effective for high-volume usage
    """
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in environment variables")
        print("Please add your ElevenLabs API key to .env file:")
        print("ELEVENLABS_API_KEY=your_api_key_here")
        sys.exit(1)
    
    try:
        from elevenlabs import ElevenLabs

        # Initialize client with API key
        client = ElevenLabs(api_key=api_key)
        
        print("ElevenLabs Turbo v2.5 TTS")
        print("=" * 40)

        # Get text from command line argument or use default
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])  # Join all arguments as text
        else:
            text = "The first move is what sets everything in motion."

        print(f"Text: {text}")
        print("Generating and playing...")
        
        try:
            # Generate audio using correct ElevenLabs v2.16.0 API
            audio = client.text_to_speech.convert(
                text=text,
                voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice ID
                model_id="eleven_turbo_v2_5"
            )

            # Save and play audio with system player
            import tempfile
            import subprocess

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                for chunk in audio:
                    f.write(chunk)
                temp_file = f.name

            print(f"Audio saved to: {temp_file}")

            # Play audio in background without opening media player UI
            try:
                # Method 1: Use PowerShell with Windows Media Foundation (background playback)
                subprocess.run([
                    "powershell", "-WindowStyle", "Hidden", "-Command",
                    f"""
                    Add-Type -AssemblyName presentationCore;
                    $player = New-Object System.Windows.Media.MediaPlayer;
                    $player.Open([uri]'{temp_file}');
                    $player.Play();
                    Start-Sleep -Seconds 5;
                    $player.Stop();
                    $player.Close()
                    """
                ], check=True, timeout=15)
            except:
                try:
                    # Method 2: Use Windows built-in mplay32 (background)
                    subprocess.run([
                        "mplay32", "/play", "/close", temp_file
                    ], check=True, timeout=10)
                except:
                    try:
                        # Method 3: PowerShell SoundPlayer (background)
                        subprocess.run([
                            "powershell", "-WindowStyle", "Hidden", "-Command",
                            f"(New-Object Media.SoundPlayer '{temp_file}').PlaySync()"
                        ], check=True, timeout=10)
                    except:
                        print(f"Could not play audio. File saved at: {temp_file}")

            # Clean up temp file after delay
            try:
                import time
                time.sleep(2)
                os.unlink(temp_file)
            except:
                pass
            print("Playback complete!")

        except Exception as e:
            print(f"Error: {e}")
        
        
    except ImportError:
        print("Error: elevenlabs package not installed")
        print("This script uses UV to auto-install dependencies.")
        print("Make sure UV is installed: https://docs.astral.sh/uv/")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()