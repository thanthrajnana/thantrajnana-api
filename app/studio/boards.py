from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Board:
    id: str
    name: str
    family: str
    fqbn: str


SUPPORTED_BOARDS: dict[str, Board] = {
    "arduino-uno": Board(
        id="arduino-uno",
        name="Arduino Uno R3",
        family="arduino",
        fqbn="arduino:avr:uno",
    ),
    "arduino-nano": Board(
        id="arduino-nano",
        name="Arduino Nano",
        family="arduino",
        fqbn="arduino:avr:nano",
    ),
    "arduino-mega": Board(
        id="arduino-mega",
        name="Arduino Mega 2560",
        family="arduino",
        fqbn="arduino:avr:mega",
    ),
    "esp32-devkit-v1": Board(
        id="esp32-devkit-v1",
        name="ESP32 DevKit V1",
        family="esp32",
        fqbn="esp32:esp32:esp32",
    ),
    "esp32-s3-devkit": Board(
        id="esp32-s3-devkit",
        name="ESP32-S3 Dev Module",
        family="esp32",
        fqbn="esp32:esp32:esp32s3",
    ),
    "esp32-c3-devkit": Board(
        id="esp32-c3-devkit",
        name="ESP32-C3 Dev Module",
        family="esp32",
        fqbn="esp32:esp32:esp32c3",
    ),
}
