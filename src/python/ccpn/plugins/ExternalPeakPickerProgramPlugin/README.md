# External Program Plugin

## Notice

This plugin is **only** a demonstration to showcase how an external program can be linked and run, exchange data via files, and update a display in real time with CcpNmr Version 3.

It is **not**:

- A production plugin
- A reliable or maintained application
- An example of coding best practices

**hard-coded** for demonstration purposes and may lack error handling, flexibility, or performance optimisations.

## Before you start

- ensure the plugin_description.json is correct.
  Open the plugin_description.json and inspect the main values,
  - name
  - version
  - entryPoint
- you have a function external program
- you have the python file and you set in the entryPoint in the json. You can find more info in the code how the entry point synthax works

## How to Use

# How to Use

1. Run the program and make sure the plugin is enabled in **Preferences → Plugins**.  
2. Open the demo spectrum located in the `ThePeakPickerProgram` directory (`GB1_HSQC.ucsf`).  
3. Load this spectrum into **Version3**.  
4. From the **Main Menu → Plugins**, select **"My External Program [DEMO]"**.  
   - A module or popup will appear.  
5. In the module:  
   - Select the **PeakList**.  
   - Select the **Output File** (you can keep the default).  
6. Click **Run**.  
   - This will launch the external program with the appropriate arguments.  
7. In the external program, pick peaks as needed, by clicking at position (ensure picking mode is ticked).  
   - Peaks will be written to `GB1_peaks.csv`.  
8. A **file watcher** monitors the output directory:  
   - When the CSV file changes, the plugin automatically updates Analysis by adding or deleting peaks.  

**That’s it! 🎉**  
Peaks from the external program are synchronised back into Analysis automatically.

