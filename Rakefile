require "rake/testtask"

Rake::TestTask.new(:test) do |t|
  t.libs << "test"
  t.test_files = FileList["test/test_*.rb"]
  t.warning = false
end

desc "Play Ashen Vault"
task :run do
  ruby "bin/ashen_vault"
end

task default: :test
