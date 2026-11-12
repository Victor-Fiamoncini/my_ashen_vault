module AshenVault
  # Maps keys to actions. An optional script ("forward:1.5 attack wait:1")
  # drives the same actions for headless smoke runs.
  class Input
    include Raylib

    KEYS = {
      forward: [KEY_W, KEY_UP], back: [KEY_S, KEY_DOWN],
      strafe_l: [KEY_A], strafe_r: [KEY_D], turn_l: [KEY_LEFT], turn_r: [KEY_RIGHT],
      look_up: [KEY_PAGE_UP], look_down: [KEY_PAGE_DOWN], sprint: [KEY_LEFT_SHIFT, KEY_RIGHT_SHIFT],
      attack: [KEY_SPACE], cast: [KEY_F], interact: [KEY_E], cycle: [KEY_R],
      menu: [KEY_TAB, KEY_I], pause: [KEY_ESCAPE], quick1: [KEY_ONE], quick2: [KEY_TWO],
      up: [KEY_W, KEY_UP], down: [KEY_S, KEY_DOWN],
      confirm: [KEY_ENTER, KEY_E, KEY_SPACE], cancel: [KEY_ESCAPE, KEY_TAB, KEY_BACKSPACE]
    }.freeze
    MOUSE = { attack: MOUSE_BUTTON_LEFT, cast: MOUSE_BUTTON_RIGHT }.freeze

    # What the Controls screen shows. Keep in sync with KEYS / MOUSE.
    CONTROLS = [
      ["Move", "W S / Up Down"], ["Strafe", "A D"], ["Sprint", "Hold Shift"],
      ["Turn / look", "Mouse, Left Right"], ["Look up / down", "PgUp PgDn"],
      ["Attack", "Space / Left mouse"], ["Cast spell", "F / Right mouse"], ["Change spell", "R"],
      ["Use, talk, open", "E"], ["Belongings", "Tab / I"], ["Red Tonic / Blue Moss", "1 / 2"],
      ["Pause", "Esc"], ["Menus", "Up Down, Enter, Esc"]
    ].freeze

    def initialize(script = nil)
      @steps = script.to_s.split.map do |tok|
        action, secs = tok.split(":")
        [action.to_sym, secs&.to_f]
      end
      @held = nil
      @held_t = 0.0
      @pressed = nil
      @wait = 0.0
    end

    def scripted? = !@steps.empty? || @held || @wait.positive?

    def update(dt)
      @pressed = nil
      if @held
        @held_t -= dt
        @held = nil if @held_t <= 0
        return
      end
      if @wait.positive?
        @wait -= dt
        return
      end
      return if @steps.empty?

      action, secs = @steps.shift
      if action == :wait
        @wait = secs || 1.0
      elsif secs
        @held = action
        @held_t = secs
      else
        @pressed = action
      end
    end

    def down?(action)
      return true if @held == action

      KEYS.fetch(action, []).any? { |k| IsKeyDown(k) } || (MOUSE.key?(action) && IsMouseButtonDown(MOUSE[action]))
    end

    def pressed?(action)
      return true if @pressed == action

      KEYS.fetch(action, []).any? { |k| IsKeyPressed(k) } ||
        (MOUSE.key?(action) && IsMouseButtonPressed(MOUSE[action]))
    end
  end
end
