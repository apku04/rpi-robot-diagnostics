# Klipper & Moonraker Installation Guide

To get the motor controller tests working, you need to install the Klipper ecosystem. We have downloaded **KIAUH** (Klipper Installation And Update Helper) to your home folder to make this easy.

## Step 1: Run KIAUH
Open a terminal and run:
```bash
~/kiauh/kiauh.sh
```

## Step 2: Install Klipper
1. In the KIAUH menu, select **1** (Install).
2. Select **1** (Klipper).
3. When asked for Python version, choose **Python 3.x**.
4. Number of instances: **1**.
5. Confirm installation.

## Step 3: Install Moonraker
1. In the Install menu, select **2** (Moonraker).
2. Confirm installation.

## Step 4: Install a Web Interface (Recommended)
To easily control the board later, install a web interface:
1. In the Install menu, select **3** (Mainsail) OR **4** (Fluidd).

## Step 5: Configuration
After installation, you will need to configure `printer.cfg` for your Octopus Pro.
1. Klipper configuration is usually located at `~/printer_data/config/printer.cfg`.
2. You will need to compile firmware for the Octopus Pro and flash it to the board (via SD card or USB DFU).

## Step 6: Verify
Run the diagnostics again:
```bash
python3 run_diagnostics.py
```
