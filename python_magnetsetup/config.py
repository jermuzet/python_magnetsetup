from decouple import Config, RepositoryEnv

# TODO load setting.env from /etc or /usr/share/python_magnetsetup
#      or a local setting from $HOME/.magnetsetup.env

data = Config(RepositoryEnv("settings.env"))
