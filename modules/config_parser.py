import json
from typing import List, Union

import confuse
import yaml

import modules.files as files
import modules.logs as logging


class YAMLElement:
    def __init__(self, data):
        self.data = data

    def _get_value(self, key: str, default=None):
        try:
            return self.data[key].get()
        except confuse.NotFoundError:
            return default
        except Exception:
            try:
                return self.data[key]
            except Exception:
                return default


class Entry(YAMLElement):
    def __init__(self, data):
        super().__init__(data)
        self.data = data

    def all_paths(self, advanced_settings: 'AdvancedConfig' = None) -> List[str]:
        paths = []
        paths.extend(self.remote_paths)

        if not advanced_settings or not advanced_settings.path_globbing.enabled:
            return paths

        local_files_root = advanced_settings.path_globbing.local_root_folder
        remote_files_root = advanced_settings.path_globbing.remote_root_folder

        for glob in self.local_path_globs:
            local_files = files.get_all_files_matching_glob_pattern(directory=local_files_root, pattern=glob)
            for local_file in local_files:
                remote_file = files.translate_local_path_to_remote_path(local_path=local_file,
                                                                        local_root_folder=local_files_root,
                                                                        remote_root_folder=remote_files_root)
                paths.append(remote_file)

        return paths

    @property
    def remote_paths(self) -> List[str]:
        return self._get_value(key="paths", default=[])

    @property
    def local_path_globs(self) -> List[str]:
        return self._get_value(key="path_globs", default=[])

    @property
    def weight(self) -> int:
        return self._get_value(key="weight", default=1)

    @property
    def disable_always(self) -> bool:
        return self._get_value(key="disable_always", default=False)


class NumericalEntry(Entry):
    def __init__(self, data):
        super().__init__(data)

    @property
    def number(self) -> int:
        return self._get_value(key="number", default=None)


class DateRangeEntry(Entry):
    def __init__(self, data):
        super().__init__(data=data)

    @property
    def name(self) -> str:
        return self._get_value(key="name", default=None)

    @property
    def start_date(self) -> str:
        return self._get_value(key="start_date", default=None)

    @property
    def end_date(self) -> str:
        return self._get_value(key="end_date", default=None)

    def __repr__(self):
        return (f"DateRangeEntry(start_date={self.start_date}, end_date={self.end_date}, "
                f"remote_paths={self.remote_paths}, local_path_globs={self.local_path_globs}, weight={self.weight})")


class WeekEntry(NumericalEntry):
    def __init__(self, data):
        super().__init__(data=data)

    def __repr__(self):
        return (f"WeekEntry(number={self.number}, remote_paths={self.remote_paths}, "
                f"local_path_globs={self.local_path_globs}, weight={self.weight})")


class MonthEntry(NumericalEntry):
    def __init__(self, data):
        super().__init__(data=data)

    def __repr__(self):
        return (f"MonthEntry(number={self.number}, remote_paths={self.remote_paths}, "
                f"local_path_globs={self.local_path_globs}, weight={self.weight})")


class ConfigSection(YAMLElement):
    def __init__(self, section_key: str, data, parent_key: str = None):
        self.section_key = section_key
        try:
            data = data[self.section_key]
        except confuse.NotFoundError:
            pass
        self._parent_key = parent_key
        super().__init__(data=data)

    @property
    def full_key(self):
        if self._parent_key is None:
            return self.section_key
        return f"{self._parent_key}_{self.section_key}".upper()

    def _get_subsection(self, key: str, default=None):
        try:
            return ConfigSection(section_key=key, parent_key=self.full_key, data=self.data)
        except confuse.NotFoundError:
            return default


class PlexServerConfig(ConfigSection):
    def __init__(self, data):
        super().__init__(section_key="plex", data=data)

    @property
    def url(self) -> str:
        return self._get_value(key="url", default="")

    @property
    def token(self) -> str:
        return self._get_value(key="token", default="")

    @property
    def port(self) -> Union[int, None]:
        port = self._get_value(key="port", default=None)
        if not port:
            # Try to parse the port from the URL
            if self.url.startswith("http://"):
                port = 80
            elif self.url.startswith("https://"):
                port = 443

        return port


class PathGlobbingConfig(ConfigSection):
    def __init__(self, data):
        super().__init__(section_key="path_globbing", data=data)

    @property
    def enabled(self) -> bool:
        return self._get_value(key="enabled", default=False)

    @property
    def local_root_folder(self) -> str:
        return self._get_value(key="root_path", default="/")

    @property
    def remote_root_folder(self) -> str:
        return self._get_value(key="plex_path", default="/")


class AdvancedConfig(ConfigSection):
    def __init__(self, data):
        super().__init__(section_key="advanced", data=data)

    @property
    def path_globbing(self) -> PathGlobbingConfig:
        return PathGlobbingConfig(data=self.data)


class ScheduleSection(ConfigSection):
    def __init__(self, section_key: str, data):
        super().__init__(section_key=section_key, data=data)

    @property
    def enabled(self) -> bool:
        return self._get_value(key="enabled", default=False)


class AlwaysSection(ScheduleSection):
    def __init__(self, data):
        super(ScheduleSection, self).__init__(section_key="always", data=data)

    # Double inheritance doesn't work well with conflicting "data" properties, just re-implement these two functions.
    def all_paths(self, advanced_settings: 'AdvancedConfig' = None) -> List[str]:
        paths = []
        paths.extend(self.remote_paths)

        if not advanced_settings or not advanced_settings.path_globbing.enabled:
            return paths

        local_files_root = advanced_settings.path_globbing.local_root_folder
        remote_files_root = advanced_settings.path_globbing.remote_root_folder

        for glob in self.local_path_globs:
            local_files = files.get_all_files_matching_glob_pattern(directory=local_files_root, pattern=glob)
            for local_file in local_files:
                remote_file = files.translate_local_path_to_remote_path(local_path=local_file,
                                                                        local_root_folder=local_files_root,
                                                                        remote_root_folder=remote_files_root)
                paths.append(remote_file)

        return paths

    @property
    def remote_paths(self) -> List[str]:
        return self._get_value(key="paths", default=[])

    @property
    def local_path_globs(self) -> List[str]:
        return self._get_value(key="path_globs", default=[])

    @property
    def weight(self) -> int:
        return self._get_value(key="weight", default=1)

    def random_count(self, advanced_settings: 'AdvancedConfig' = None) -> int:
        return self._get_value(key="count", default=len(self.all_paths(advanced_settings=advanced_settings)))

    def __repr__(self):
        return (f"AlwaysSection(remote_paths={self.remote_paths}, local_path_globs={self.local_path_globs}, "
                f"weight={self.weight}")


class DateRangeSection(ScheduleSection):
    def __init__(self, data):
        super().__init__(section_key="date_range", data=data)

    @property
    def ranges(self) -> List[DateRangeEntry]:
        data = self._get_value(key="ranges", default=[])
        return [DateRangeEntry(data=d) for d in data]

    @property
    def range_count(self) -> int:
        return len(self.ranges)


class WeeklySection(ScheduleSection):
    def __init__(self, data):
        super().__init__(section_key="weekly", data=data)

    @property
    def weeks(self) -> List[WeekEntry]:
        data = self._get_value(key="weeks", default=[])
        return [WeekEntry(data=d) for d in data]

    @property
    def week_count(self) -> int:
        return len(self.weeks)


class MonthlySection(ScheduleSection):
    def __init__(self, data):
        super().__init__(section_key="monthly", data=data)

    @property
    def months(self) -> List[MonthEntry]:
        data = self._get_value(key="months", default=[])
        return [MonthEntry(data=d) for d in data]

    @property
    def month_count(self) -> int:
        return len(self.months)


class Config:
    def __init__(self, app_name: str, config_path: str):
        self.config = confuse.Configuration(app_name)

        # noinspection PyBroadException
        try:
            self.config.set_file(filename=config_path)
            logging.debug(f"Loaded config from {config_path}")
        except Exception:  # pylint: disable=broad-except # not sure what confuse will throw
            raise FileNotFoundError(f"Config file not found: {config_path}")

        self.plex = PlexServerConfig(data=self.config)
        self.always = AlwaysSection(data=self.config)
        self.date_ranges = DateRangeSection(data=self.config)
        self.monthly = MonthlySection(data=self.config)
        self.weekly = WeeklySection(data=self.config)
        self.advanced = AdvancedConfig(data=self.config)

        logging.debug(f"Using configuration:\n{self.log()}")

    def __repr__(self) -> str:
        raw_yaml_data = self.config.dump()
        json_data = yaml.load(raw_yaml_data, Loader=yaml.FullLoader)
        return json.dumps(json_data, indent=4)

    @property
    def all(self) -> dict:
        return {
            "Plex - URL": self.plex.url,
            "Plex - Token": "Exists" if self.plex.token else "Not Set",
            "Always - Enabled": self.always.enabled,
            "Always - Paths": self.always.all_paths(advanced_settings=self.advanced),
            "Always - Count": self.always.random_count(advanced_settings=self.advanced),
            "Always - Weight": self.always.weight,
            "Date Range - Enabled": self.date_ranges.enabled,
            "Date Range - Ranges": self.date_ranges.ranges,
            "Monthly - Enabled": self.monthly.enabled,
            "Monthly - Months": self.monthly.months,
            "Weekly - Enabled": self.weekly.enabled,
            "Weekly - Weeks": self.weekly.weeks,
            "Advanced - Path Globbing - Enabled": self.advanced.path_globbing.enabled,
            "Advanced - Path Globbing - Local Root Folder": self.advanced.path_globbing.local_root_folder,
            "Advanced - Path Globbing - Remote Root Folder": self.advanced.path_globbing.remote_root_folder
        }

    def log(self) -> str:
        return "\n".join([f"{key}: {value}" for key, value in self.all.items()])
