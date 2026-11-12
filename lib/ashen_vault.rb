require "raylib"

lib_dir = File.join(Gem::Specification.find_by_name("raylib-bindings").full_gem_path, "lib")
Raylib.load_lib(File.join(lib_dir, "libraylib.#{RUBY_PLATFORM.start_with?('x86_64') ? 'x86_64' : 'aarch64'}.so"))

require_relative "ashen_vault/core"
require_relative "ashen_vault/render/texture_gen"
require_relative "ashen_vault/render/mesh_builder"
require_relative "ashen_vault/render/gpu"
require_relative "ashen_vault/render/rig"
require_relative "ashen_vault/render/models"
require_relative "ashen_vault/world/world"
require_relative "ashen_vault/audio/synth"
require_relative "ashen_vault/input"
require_relative "ashen_vault/ui/hud"
require_relative "../data/dialogue"
require_relative "ashen_vault/game"
