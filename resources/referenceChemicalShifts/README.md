# Reference ChemicalShifts file template documentation

New reference chemicalShifts need to be in a JSON file.
See the Template for the general structure.

## Top Level:

**title**: Mandatory. Str. A short one/two word title.  This will appear in the GUI as an entry in ReferenceChemicalShifts selection widget(s)

**comment**: Mandatory. Str. A brief explanation of what the file contains.  This message will appear in the GUI tooltips for the selection widget(s)

**applicationVersion**: Mandatory. Str. The CcpNmr version used when creating this file

**creation_date_dd-mm-yy**: Mandatory. Str. The creation date in the format dd-mm-yy

**fileVersion**: Optional. Str. This file version

**user**: Optional. Str. Who created the file

**moleculeType**: Mandatory. Str. The molecule type described in the file

**residues**:  Mandatory. List of dictionaries. Category containing information about  the residues. Open new level:  ***Residue Level*** , see below.

## **Residue Level**

**residueName**: Mandatory. Str. The residue name. Three letter code for protein. E.g.: Alanine

**shortName**: Mandatory. Str. The residue short name. Three letter code for protein, Two letter code for DNA, etc. E.g.: ALA

**ccpcode**: Optional. Str. The unique ccp code if available. E.g.: Ala

**atoms**: Mandatory. List of dictionaries. Category containing information about the residue atoms. Open new level:  ***Atom Level*** , see below.

## Atom level:

**atomName**: Mandatory. Str. The atom name. NEF nomenclature. E.g.: HB%

**element**: Mandatory. Str. The atom element name. E.g.: H

**averageShift**: Mandatory. Float. The atom average chemical shift in ppm. E.g.: 1.352

**stdShift**: Mandatory. Float. The atom standard deviation of all observed chemical shifts. E.g.: 0.277

**minShift**:Optional. Float. The atom minimal observed chemical shift in ppm. E.g.: -14.040

**maxShift**:Optional. Float. The atom maximum observed chemical shift in ppm. E.g.: 5.48

The following information is needed only to accurately plot the distribution curve on the Reference ChemicalShifts GUI module.

**distribution**: Optional. List. The individually observed chemical shift Y values for plotting the distribution curve

**distributionRefValue**: Optional. Float. The reference value of the distribution list.  Mandatory if the distribution list is given

**distributionValuePerPoint**: Optional. Float. The value per point needed for recreating the X axis of the distribution. Mandatory if the distribution list is given
