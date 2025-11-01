# Voice Integration (Wispr + TTS Approach)

## Overview

**Phase 2 Feature**: Toggle-able text-to-speech output with swappable providers

**Approach**: Simple and flexible
- **Input**: User manages Wispr Flow (external to Brain CLI)
- **Output**: Toggle-able TTS with multiple provider options
- **No OpenAI Realtime API** (avoids complexity)

## Why This Approach

### Advantages
- ✅ **Simple**: No WebSocket complexity
- ✅ **Flexible**: Swap TTS providers easily
- ✅ **Agent-Agnostic**: Works with any orchestrator
- ✅ **Free Option**: pyttsx3 is local and free
- ✅ **Privacy**: Can use local-only TTS
- ✅ **Optional**: Easy to toggle on/off

### vs OpenAI Realtime API
- ❌ OpenAI Realtime: Complex WebSocket management
- ❌ OpenAI Realtime: Locks into OpenAI ecosystem
- ❌ OpenAI Realtime: State synchronization issues
- ❌ OpenAI Realtime: Expensive ($0.06-$0.24 per minute)
- ✅ Our Approach: Simple, flexible, cheaper

## Input: Wispr Flow (User Managed)

### What is Wispr Flow
- Mac app for voice-to-text
- Works system-wide
- User's existing subscription (~$10/month)
- External to Brain CLI

### Integration
**User workflow**:
1. Launch Brain CLI in terminal
2. Press Wispr hotkey (user-configured)
3. Speak command
4. Wispr transcribes to terminal
5. Brain CLI processes text

**Brain CLI doesn't need to integrate** - Wispr handles all input.

## Output: Toggle-able TTS

### Architecture

```
Brain CLI Response
    ↓
TTS Manager (if enabled)
    ↓
Selected Provider (pyttsx3, ElevenLabs, Google, OpenAI, Coqui)
    ↓
Audio Output
```

### TTS Manager Implementation

```python
# src/brain/tts.py
import pyttsx3
from abc import ABC, abstractmethod
from typing import Optional
import re

class TTSProvider(ABC):
    """Base class for TTS providers"""

    @abstractmethod
    def speak(self, text: str):
        """Speak text"""
        pass

    @abstractmethod
    def configure(self, **kwargs):
        """Configure provider settings"""
        pass

    def clean_text_for_speech(self, text: str) -> str:
        """Clean markdown and formatting for speech"""
        # Remove code blocks
        text = re.sub(r'```.*?```', '[code block]', text, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Remove bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

        # Remove italics
        text = re.sub(r'\*([^*]+)\*', r'\1', text)

        # Remove links (keep text, discard URL)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove headers
        text = re.sub(r'#+\s+', '', text)

        # Remove list markers
        text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

class Pyttsx3Provider(TTSProvider):
    """Local TTS using pyttsx3 (FREE)"""

    def __init__(self):
        self.engine = pyttsx3.init()
        self.configure()

    def speak(self, text: str):
        clean_text = self.clean_text_for_speech(text)
        self.engine.say(clean_text)
        self.engine.runAndWait()

    def configure(self, rate: int = 150, volume: float = 0.9, voice: Optional[str] = None):
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)

        if voice:
            voices = self.engine.getProperty('voices')
            for v in voices:
                if voice.lower() in v.name.lower():
                    self.engine.setProperty('voice', v.id)
                    break

class GoogleTTSProvider(TTSProvider):
    """Google TTS (FREE, cloud-based)"""

    def __init__(self):
        try:
            from gtts import gTTS
            import tempfile
            import os
            self.gTTS = gTTS
            self.lang = 'en'
        except ImportError:
            raise ImportError("Install gTTS: pip install gTTS")

    def speak(self, text: str):
        import tempfile
        import os
        import subprocess

        clean_text = self.clean_text_for_speech(text)

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file = f.name

        try:
            # Generate speech
            tts = self.gTTS(text=clean_text, lang=self.lang, slow=False)
            tts.save(temp_file)

            # Play audio (macOS)
            subprocess.run(['afplay', temp_file], check=True)
        finally:
            os.unlink(temp_file)

    def configure(self, lang: str = 'en', **kwargs):
        self.lang = lang

class ElevenLabsProvider(TTSProvider):
    """ElevenLabs TTS (PAID: $5-22/month)"""

    def __init__(self, api_key: str):
        try:
            from elevenlabs import generate, set_api_key, play
            self.generate = generate
            self.play = play
            set_api_key(api_key)
            self.voice = "Adam"
        except ImportError:
            raise ImportError("Install elevenlabs: pip install elevenlabs")

    def speak(self, text: str):
        clean_text = self.clean_text_for_speech(text)
        audio = self.generate(text=clean_text, voice=self.voice)
        self.play(audio)

    def configure(self, voice: str = "Adam", **kwargs):
        self.voice = voice

class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS (PAID: ~$0.015 per 1K chars)"""

    def __init__(self, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.voice = "alloy"
        self.model = "tts-1"

    def speak(self, text: str):
        import tempfile
        import os
        import subprocess

        clean_text = self.clean_text_for_speech(text)

        # Generate speech
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=clean_text
        )

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            temp_file = f.name
            response.stream_to_file(temp_file)

        try:
            # Play audio
            subprocess.run(['afplay', temp_file], check=True)
        finally:
            os.unlink(temp_file)

    def configure(self, voice: str = "alloy", model: str = "tts-1", **kwargs):
        self.voice = voice
        self.model = model

class CoquiTTSProvider(TTSProvider):
    """Coqui TTS - Local neural TTS (FREE, high quality)"""

    def __init__(self):
        try:
            from TTS.api import TTS
            self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
        except ImportError:
            raise ImportError("Install TTS: pip install TTS")

    def speak(self, text: str):
        import tempfile
        import os
        import subprocess

        clean_text = self.clean_text_for_speech(text)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            temp_file = f.name

        try:
            self.tts.tts_to_file(text=clean_text, file_path=temp_file)
            subprocess.run(['afplay', temp_file], check=True)
        finally:
            os.unlink(temp_file)

    def configure(self, **kwargs):
        pass

class TTSManager:
    """Main TTS manager"""

    PROVIDERS = {
        'pyttsx3': Pyttsx3Provider,
        'google': GoogleTTSProvider,
        'elevenlabs': ElevenLabsProvider,
        'openai': OpenAITTSProvider,
        'coqui': CoquiTTSProvider
    }

    def __init__(self):
        self.enabled = False
        self.provider: Optional[TTSProvider] = None
        self.provider_name = None

    def toggle(self, provider: str = 'pyttsx3', **config):
        """Toggle TTS on/off"""
        if self.enabled:
            self.enabled = False
            self.provider = None
            return f"🔇 TTS disabled"
        else:
            try:
                provider_class = self.PROVIDERS.get(provider)
                if not provider_class:
                    return f"❌ Unknown provider: {provider}. Options: {list(self.PROVIDERS.keys())}"

                # Initialize provider
                if provider in ['elevenlabs', 'openai']:
                    api_key = config.get('api_key') or os.getenv(f"{provider.upper()}_API_KEY")
                    if not api_key:
                        return f"❌ {provider} requires API key"
                    self.provider = provider_class(api_key)
                else:
                    self.provider = provider_class()

                # Configure
                self.provider.configure(**config)

                self.enabled = True
                self.provider_name = provider
                return f"🔊 TTS enabled ({provider})"

            except ImportError as e:
                return f"❌ {e}"
            except Exception as e:
                return f"❌ TTS initialization failed: {e}"

    def speak(self, text: str):
        """Speak text if enabled"""
        if self.enabled and self.provider:
            try:
                self.provider.speak(text)
            except Exception as e:
                print(f"⚠️ TTS error: {e}")

    def change_provider(self, provider: str, **config):
        """Change TTS provider without disabling"""
        was_enabled = self.enabled
        if was_enabled:
            self.toggle()  # Disable current

        result = self.toggle(provider, **config)  # Enable new

        return result

    def get_status(self) -> str:
        """Get current TTS status"""
        if self.enabled:
            return f"🔊 TTS: {self.provider_name}"
        else:
            return "🔇 TTS: disabled"
```

## Integration with Brain CLI

### In REPL

```python
# src/brain/cli.py

from .tts import TTSManager

def main(workspace: str, agent: str, prompt: str):
    # ... existing setup

    # Initialize TTS
    tts = TTSManager()

    # REPL loop
    while True:
        try:
            user_input = console.input("[bold blue]>[/bold blue] ")

            # ... handle slash commands

            # Execute task
            response = orchestrator.execute(user_input)

            # Display response
            console.print(Markdown(response))

            # TTS output (if enabled)
            if tts.enabled:
                tts.speak(response)

        except KeyboardInterrupt:
            break
```

### Slash Commands

```python
def handle_slash_command(cmd: str, args: List[str], tts: TTSManager, console: Console):
    # ... existing commands

    elif command == 'tts':
        if not args:
            console.print(f"Current: {tts.get_status()}")
            console.print("\nUsage:")
            console.print("  /tts on [provider]     - Enable TTS")
            console.print("  /tts off               - Disable TTS")
            console.print("  /tts provider <name>   - Change provider")
            console.print("\nProviders: pyttsx3 (free), google (free), elevenlabs (paid), openai (paid), coqui (free)")
            return

        action = args[0].lower()

        if action in ['on', 'enable']:
            provider = args[1] if len(args) > 1 else 'pyttsx3'
            result = tts.toggle(provider)
            console.print(result)

        elif action in ['off', 'disable']:
            if tts.enabled:
                result = tts.toggle()
                console.print(result)
            else:
                console.print("TTS already disabled")

        elif action == 'provider':
            if len(args) < 2:
                console.print("[red]Usage: /tts provider <name>[/red]")
                return
            provider = args[1]
            result = tts.change_provider(provider)
            console.print(result)

        elif action == 'status':
            console.print(tts.get_status())

        else:
            console.print(f"[red]Unknown action: {action}[/red]")
```

## Configuration

### Config File

```yaml
# ~/.brain-config.yaml
tts:
  enabled: false
  default_provider: pyttsx3
  providers:
    pyttsx3:
      rate: 150
      volume: 0.9
      voice: null  # Use system default

    google:
      lang: en

    elevenlabs:
      api_key: ${ELEVENLABS_API_KEY}
      voice: Adam

    openai:
      api_key: ${OPENAI_API_KEY}
      voice: alloy
      model: tts-1

    coqui:
      model: tts_models/en/ljspeech/tacotron2-DDC
```

### Load Config

```python
def load_tts_config(config_file: str, provider: str) -> dict:
    """Load TTS configuration"""
    with open(os.path.expanduser(config_file)) as f:
        config = yaml.safe_load(f)

    tts_config = config.get('tts', {})
    provider_config = tts_config.get('providers', {}).get(provider, {})

    return provider_config
```

## Provider Comparison

| Provider | Cost | Quality | Speed | Privacy | Requires Internet |
|----------|------|---------|-------|---------|-------------------|
| **pyttsx3** | FREE | ⭐⭐ | ⚡⚡⚡ | ✅ Local | ❌ No |
| **Google TTS** | FREE | ⭐⭐⭐ | ⚡⚡ | ❌ Cloud | ✅ Yes |
| **Coqui** | FREE | ⭐⭐⭐⭐ | ⚡ | ✅ Local | ❌ No |
| **ElevenLabs** | $5-22/mo | ⭐⭐⭐⭐⭐ | ⚡⚡ | ❌ Cloud | ✅ Yes |
| **OpenAI TTS** | $0.015/1K | ⭐⭐⭐⭐ | ⚡⚡ | ❌ Cloud | ✅ Yes |

### Recommendations

**For FREE + Privacy**: pyttsx3 or Coqui
**For FREE + Quality**: Google TTS or Coqui
**For BEST Quality**: ElevenLabs
**For Good Balance**: OpenAI TTS

## Usage Examples

### Basic Usage

```bash
# Start Brain CLI
brain --workspace default

# Enable TTS (free, local)
> /tts on

# Ask question - response will be spoken
> What is quantum computing?

# Disable TTS
> /tts off
```

### Change Provider

```bash
# Start with pyttsx3 (default)
> /tts on

# Switch to Google TTS (free, cloud)
> /tts provider google

# Switch to ElevenLabs (premium)
> /tts provider elevenlabs

# Check status
> /tts status
```

### Configure Voice

```python
# In config or via code
tts.toggle('pyttsx3', rate=180, voice='Alex')
tts.toggle('openai', voice='nova', model='tts-1-hd')
tts.toggle('elevenlabs', voice='Bella')
```

## Text Cleaning for Speech

The TTS manager automatically cleans text:
- Removes markdown formatting
- Removes code blocks
- Removes links (keeps text)
- Removes headers and list markers
- Normalizes whitespace

**Example**:
```
Input: "Here's the **answer**: `code` and [link](url)"
Spoken: "Here's the answer: code and link"
```

## Installation

### pyttsx3 (FREE, local)
```bash
pip install pyttsx3

# macOS: No additional deps
# Linux: sudo apt-get install espeak
# Windows: Included
```

### Google TTS (FREE, cloud)
```bash
pip install gTTS
```

### Coqui TTS (FREE, local, high quality)
```bash
pip install TTS

# First run downloads model (~100MB)
```

### ElevenLabs (PAID)
```bash
pip install elevenlabs

# Get API key from elevenlabs.io
# Plans: $5, $22, $99/month
```

### OpenAI TTS (PAID)
```bash
# Already have openai package
pip install openai

# Uses existing OpenAI API key
# Cost: ~$0.015 per 1K characters
```

## Future Enhancements (Phase 4+)

### OpenAI Realtime API (Optional)
- Full-duplex voice conversation
- Lower latency
- More natural interaction
- **But**: Much more complex, expensive

**Only implement if**:
- Strong user demand
- Phase 1-3 prove valuable
- Budget allows (~$0.06-$0.24 per minute)

### Voice Profiles
- Save preferred voice settings per workspace
- Different voices for different agents
- Emotional tone based on response type

### Smart Interruption
- Detect when user starts speaking
- Pause/stop TTS automatically
- Resume or skip based on context

### Selective TTS
- Only speak summaries, not full responses
- Skip code blocks entirely
- Highlight key points with emphasis

## Testing

```python
# Test TTS functionality
def test_tts():
    tts = TTSManager()

    # Test pyttsx3 (free)
    result = tts.toggle('pyttsx3')
    assert tts.enabled
    tts.speak("Testing text to speech")

    # Test provider switching
    result = tts.change_provider('google')
    assert tts.provider_name == 'google'
    tts.speak("Testing Google TTS")

    # Disable
    tts.toggle()
    assert not tts.enabled

if __name__ == '__main__':
    test_tts()
```

## Summary

**Voice Integration Strategy**:
- ✅ **Input**: User manages Wispr Flow (external)
- ✅ **Output**: Toggle-able TTS with 5 provider options
- ✅ **Simple**: No WebSocket complexity
- ✅ **Flexible**: Swap providers anytime
- ✅ **Free Option**: pyttsx3 works offline
- ✅ **Optional**: Easy to disable

**Phase 2 Implementation**:
- TTS Manager with provider abstraction
- 5 providers: pyttsx3, Google, Coqui, ElevenLabs, OpenAI
- Slash commands for control
- Config file for preferences
- Text cleaning for natural speech

**No OpenAI Realtime** (Phase 1-3):
- Avoids complexity
- Maintains agent-agnostic design
- Keeps costs lower
- Optional for Phase 4 if demand exists

**Result**: Simple, flexible voice output that enhances the experience without adding complexity or lock-in.
