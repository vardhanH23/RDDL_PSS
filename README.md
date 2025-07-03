# RDDL PIP Automation Task

Automates downloading log/xml files, uploading to R&D Data Lake, and cleaning up.

## Setup

1. Clone the repo:
   ```sh
   git clone https://gitlab.intra.infineon.com/ifx/innersource/icw-iot-testdev/rddl_pip_automationtask.git
   cd rddl_pip_automationtask/AfterAuth
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Set environment variables:
   - `RDDL_API_TOKEN` (required)
   - `BASE_URL` (optional, default provided)

## Usage

Run the main script:
```sh
python src/data_lake_uploader.py
```

## Testing

```sh
pytest
```
