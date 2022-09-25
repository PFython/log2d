from log2d import Log

progress = Log("progress", "info", to_file=False, fmt=Log.presets[3], datefmt=Log.date_formats[1])
Log.progress.info("And so it begins...")
Log.progress.warning("Yet it must surely end.")
progress("Shortcut to log text at default/effective logging level")

s_log = Log("selenium", "debug", to_stdout=False, mode="w")
Log.selenium.debug("A typical message from Selenium...")
s_log("More selenium output...")

def count123(end):
    Log("results", mode="w")
    for i in range(1, end):
        Log.results.info(f"Counting as far a {i}")
