import json
import os
from typing import List, Union

import confuse
import yaml

import modules.files as files
import modules.logs as logging
from consts import AUTO_GENERATED_PREROLLS_DIR, AUTO_GENERATED_RECENTLY_ADDED_PREROLL_PREFIX


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


class PathGlobbingPairConfig(YAMLElement):
    def __init__(self, data):
        super().__init__(data=data)

    @property
    def local_root_folder(self) -> str:
        return self._get_value(key="root_path", default="/")

    @property
    def remote_root_folder(self) -> str:
        return self._get_value(key="plex_path", default="/")

    @property
    def patterns(self) -> List[str]:
        return self._get_value(key="patterns", default=[])

    def __repr__(self):
        return (f"PathGlobbingPairConfig(local_root_folder={self.local_root_folder}, "
                f"remote_root_folder={self.remote_root_folder}, "
                f"patterns={self.patterns})")


class PathGlobbingConfig(YAMLElement):
    def __init__(self, data):
        super().__init__(data=data)

    @property
    def enabled(self) -> bool:
        return self._get_value(key="enabled", default=False)

    @property
    def pairs(self) -> List[PathGlobbingPairConfig]:
        data = self._get_value(key="pairs", default=[])
        return [PathGlobbingPairConfig(data=d) for d in data]

    def __repr__(self):
        return f"PathGlobbingConfig(enabled={self.enabled}, pairs={self.pairs})"


class Entry(YAMLElement):
    def __init__(self, data):
        super().__init__(data)
        self.data = data

    def all_paths(self, advanced_settings: 'AdvancedConfig' = None) -> List[str]:
        paths = []
        paths.extend(self.remote_paths)

        if not self.path_globbing or not self.path_globbing.enabled:
            return paths

        for pair in self.path_globbing.pairs:
            local_files_root = pair.local_root_folder
            remote_files_root = pair.remote_root_folder
            for pattern in pair.patterns:
                local_files = files.get_all_files_matching_glob_pattern(directory=local_files_root, pattern=pattern)
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
    def path_globbing(self) -> PathGlobbingConfig:
        data = self._get_value(key="path_globbing", default={})
        return PathGlobbingConfig(data=data)

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
                f"remote_paths={self.remote_paths}, path_globbing={self.path_globbing}, weight={self.weight})")


class WeekEntry(NumericalEntry):
    def __init__(self, data):
        super().__init__(data=data)

    def __repr__(self):
        return (f"WeekEntry(number={self.number}, remote_paths={self.remote_paths}, "
                f"path_globbing={self.path_globbing}, weight={self.weight})")


class MonthEntry(NumericalEntry):
    def __init__(self, data):
        super().__init__(data=data)

    def __repr__(self):
        return (f"MonthEntry(number={self.number}, remote_paths={self.remote_paths}, "
                f"path_globbing={self.path_globbing}, weight={self.weight})")


class RunConfig(ConfigSection):
    def __init__(self, data):
        super().__init__(section_key="run", data=data)

    @property
    def schedule(self) -> str:
        return self._get_value(key="schedule", default="0 0 * * *")

    @property
    def dry_run(self) -> bool:
        return self._get_value(key="dry_run", default=False)


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


class RecentlyAddedAutoGenerationConfig(ConfigSection):
    def __init__(self, data, parent: 'AutoGenerationConfig'):
        self._parent = parent
        super().__init__(section_key="recently_added", data=data)

    @property
    def enabled(self) -> bool:
        return self._get_value(key="enabled", default=False)

    @property
    def count(self) -> int:
        return self._get_value(key="count", default=10)

    @property
    def remote_files_root(self) -> str:
        # The Plex-aware equivalent of the local (internal) path where auto-generated prerolls will be stored
        return f"{self._parent.remote_path_root}/Recently Added"

    @property
    def local_files_root(self) -> str:
        # The local (internal) path where auto-generated prerolls will be stored
        return f"{self._parent.local_path_root}/Recently Added"

    # Double inheritance doesn't work well with conflicting "data" properties, just re-implement these two functions.
    def all_paths(self, advanced_settings: 'AdvancedConfig' = None) -> List[str]:
        paths = []

        local_files = files.get_all_files_matching_glob_pattern(directory=self.local_files_root,
                                                                pattern=f"{AUTO_GENERATED_RECENTLY_ADDED_PREROLL_PREFIX}*")
        for local_file in local_files:
            remote_file = files.translate_local_path_to_remote_path(local_path=local_file,
                                                                    local_root_folder=self.local_files_root,
                                                                    remote_root_folder=self.remote_files_root)
            paths.append(remote_file)

        return paths
    
    @property
    def excluded_libraries(self) -> List[str]:
        raw = self._get_value(key="excluded_libraries", default=[])
        # Ensure it's a list even if someone types a comma-separated string
        if isinstance(raw, str):
            return [lib.strip().lower() for lib in raw.split(',') if lib.strip()]
        elif isinstance(raw, list):
            return [lib.strip().lower() for lib in raw]
        else:
            return []

    @property
    def trailer_cutoff_year(self) -> int:
        return self._get_value(key="trailer_cutoff_year", default=1980)


class AutoGenerationConfig(ConfigSection):
    def __init__(self, data):
        super().__init__(section_key="auto_generation", data=data)

    @property
    def remote_path_root(self) -> str:
        # The Plex-aware equivalent of the local (internal) path where auto-generated prerolls will be stored
        return self._get_value(key="plex_path", default=self.local_path_root)

    @property
    def local_path_root(self) -> str:
        # The local (internal) path where auto-generated prerolls will be stored
        return AUTO_GENERATED_PREROLLS_DIR

    @property
    def cookies_file(self) -> str:
        cookies_file_path = "/config/yt_dlp_cookies.txt"
        return cookies_file_path if os.path.exists(cookies_file_path) else ""

    @property
    def recently_added(self) -> RecentlyAddedAutoGenerationConfig:
        return RecentlyAddedAutoGenerationConfig(data=self.data, parent=self)


class AdvancedConfig(ConfigSection):
    def __init__(self, data):
        super().__init__(section_key="advanced", data=data)

    @property
    def auto_generation(self) -> AutoGenerationConfig:
        return AutoGenerationConfig(data=self.data)


class ScheduleSection(ConfigSection):
    def __init__(self, section_key: str, data):
        super().__init__(section_key=section_key, data=data)

    @property
    def enabled(self) -> bool:
        return self._get_value(key="enabled", default=False)


class AlwaysSection(ScheduleSection):
    def __init__(self, data):
        super(ScheduleSection, self).__init__(section_key="always", data=data)

    # Double inheritance doesn't work well with conflicting "data" properties, just re-implement these functions
    def all_paths(self, advanced_settings: 'AdvancedConfig' = None) -> List[str]:
        paths = []
        paths.extend(self.remote_paths)

        if not self.path_globbing or not self.path_globbing.enabled:
            return paths

        for pair in self.path_globbing.pairs:
            local_files_root = pair.local_root_folder
            remote_files_root = pair.remote_root_folder
            for pattern in pair.patterns:
                local_files = files.get_all_files_matching_glob_pattern(directory=local_files_root, pattern=pattern)
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
    def path_globbing(self) -> PathGlobbingConfig:
        data = self._get_value(key="path_globbing", default={})
        return PathGlobbingConfig(data=data)

    @property
    def weight(self) -> int:
        return self._get_value(key="weight", default=1)

    def random_count(self, advanced_settings: 'AdvancedConfig' = None) -> int:
        return self._get_value(key="count", default=len(self.all_paths(advanced_settings=advanced_settings)))

    def __repr__(self):
        return (f"AlwaysSection(remote_paths={self.remote_paths}, path_globbing={self.path_globbing}, "
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

        self.run = RunConfig(data=self.config)
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
            "Run - Schedule": self.run.schedule,
            "Run - Dry Run": self.run.dry_run,
            "Plex - URL": self.plex.url,
            "Plex - Token": "Exists" if self.plex.token else "Not Set",
            "Always - Enabled": self.always.enabled,
            "Always - Config": self.always,
            "Date Range - Enabled": self.date_ranges.enabled,
            "Date Range - Ranges": self.date_ranges.ranges,
            "Monthly - Enabled": self.monthly.enabled,
            "Monthly - Months": self.monthly.months,
            "Weekly - Enabled": self.weekly.enabled,
            "Weekly - Weeks": self.weekly.weeks,
            "Advanced - Auto Generation - Remote Path Root": self.advanced.auto_generation.remote_path_root,
            "Advanced - Auto Generation - Recently Added - Enabled": self.advanced.auto_generation.recently_added.enabled,
            "Advanced - Auto Generation - Recently Added - Count": self.advanced.auto_generation.recently_added.count,
            "Advanced - Auto Generation - Recently Added - Trailer Cutoff Year": self.advanced.auto_generation.recently_added.trailer_cutoff_year,
        }

    def log(self) -> str:
        return "\n".join([f"{key}: {value}" for key, value in self.all.items()])
