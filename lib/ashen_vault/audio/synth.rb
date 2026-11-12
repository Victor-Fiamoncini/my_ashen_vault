module AshenVault
  # Generates every sound effect at startup as 16-bit mono WAV data.
  module Synth
    RATE = 22_050

    module_function

    def wav(samples)
      pcm = samples.map { |s| (s.clamp(-1.0, 1.0) * 32_000).round }.pack("s<*")
      ["RIFF", 36 + pcm.bytesize, "WAVE", "fmt ", 16, 1, 1, RATE, RATE * 2, 2, 16, "data", pcm.bytesize]
        .pack("A4VA4A4VvvVVvvA4V") + pcm
    end

    def gen(seconds)
      n = (seconds * RATE).round
      Array.new(n) { |i| yield(i.to_f / RATE, i.to_f / n) }
    end

    def env(p, attack = 0.02) = p < attack ? p / attack : (1 - p)**2

    def noise = rand * 2 - 1

    def sounds
      lp = 0.0
      {
        swing: gen(0.22) do |_t, p|
          lp += (noise - lp) * (0.05 + p * 0.25)
          lp * env(p, 0.3) * 1.6
        end,
        hit: gen(0.18) { |t, p| (Math.sin(t * 2 * Math::PI * (140 - p * 80)) * 0.8 + noise * 0.4) * env(p, 0.01) },
        hurt: gen(0.3) { |t, p| (Math.sin(t * 2 * Math::PI * (220 - p * 120)) + noise * 0.3) * 0.6 * env(p, 0.01) },
        door: gen(0.9) do |t, p|
          lp += (noise - lp) * 0.02
          (lp * 3 + Math.sin(t * 2 * Math::PI * 55) * 0.3) * env(p, 0.1)
        end,
        chest: gen(0.35) { |t, p| Math.sin(t * 2 * Math::PI * (300 + p * 200)) * 0.25 * env(p, 0.05) + noise * 0.1 * (1 - p) },
        pickup: gen(0.4) { |t, p| (Math.sin(t * 2 * Math::PI * (p < 0.5 ? 660 : 880)) * 0.35) * env(p, 0.02) },
        spell: gen(0.5) do |t, p|
          lp += (noise - lp) * 0.15
          (lp * 0.8 + Math.sin(t * 2 * Math::PI * (400 + Math.sin(t * 40) * 60)) * 0.2) * env(p, 0.15)
        end,
        enemy_die: gen(0.7) { |t, p| (Math.sin(t * 2 * Math::PI * (180 - p * 140)) * 0.5 + noise * 0.3 * (1 - p)) * env(p, 0.01) },
        levelup: gen(0.9) do |t, p|
          f = [523.25, 659.25, 783.99, 1046.5][[(p * 4).floor, 3].min]
          Math.sin(t * 2 * Math::PI * f) * 0.3 * (1 - p)
        end,
        save: gen(1.2) { |t, p| (Math.sin(t * 2 * Math::PI * 392) + Math.sin(t * 2 * Math::PI * 588)) * 0.18 * env(p, 0.2) },
        bell: gen(3.0) do |t, p|
          [1.0, 2.4, 3.0, 4.5].sum { |h| Math.sin(t * 2 * Math::PI * 196 * h) / h } * 0.25 * (1 - p)**3
        end,
        step: gen(0.08) do |_t, p|
          lp += (noise - lp) * 0.3
          lp * 0.5 * env(p, 0.05)
        end
      }.transform_values { |samples| wav(samples) }
    end
  end

  # Plays synthesized sounds through raylib; silently does nothing without an audio device.
  class Audio
    include Raylib

    def initialize
      InitAudioDevice()
      @ready = IsAudioDeviceReady()
      @sounds = {}
      return unless @ready

      Synth.sounds.each do |name, bytes|
        buf = FFI::MemoryPointer.from_string(bytes)
        wave = LoadWaveFromMemory(".wav", buf, bytes.bytesize)
        @sounds[name] = LoadSoundFromWave(wave)
        UnloadWave(wave)
      end
    end

    def play(name, volume: 1.0)
      return unless @ready && (s = @sounds[name])

      SetSoundVolume(s, volume)
      PlaySound(s)
    end

    def close
      CloseAudioDevice() if @ready
    end
  end
end
