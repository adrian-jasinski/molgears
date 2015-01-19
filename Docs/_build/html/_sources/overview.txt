.. _Overview:


**********************************
An overview of the MolGears
**********************************

.. _what-is-it:

What is it?
===============================================================

This is a opensorce framework/database/toolkit based on a 
`TurboGears <http://turbogears.org/>`_ web framework and `RDKit <http://www.rdkit.org>`_
open source toolkit for cheminformatics:
 
 * programed in Python2.7 language
 * BSD license
 * source code on Github (`<https://github.com/admed/molgears>`_)
 
 .. _dependencies:
 
Software Dependencies/Third-party software component
===============================================================

 * RDKiT (`<http://www.rdkit.org>`_)
 * TurboGears (`<http://turbogears.org/>`_)
 * Postgresql Database (`<http://www.postgresql.org/>`_)
 * RDKit database cartridge for postgresql (`<http://www.rdkit.org/docs/Cartridge.html>`_)
 * Genshi (`<http://genshi.edgewall.org/>`_)
 * JSME editor (`<http://peter-ertl.com/jsme/>`_)
 * Python based libraries:
    * SQLAlchemy (`<http://www.sqlalchemy.org/>`_)
    * razi (`<http://razi.readthedocs.org/en/latest/index.html>`_)
    * Numpy (`<http://www.numpy.org/>`_)
    * Scipy (`<http://www.scipy.org/>`_)
    * Matplotlib (`<http://matplotlib.org/>`_)
    * Xlwt & Xlrd (`<http://www.python-excel.org/>`_)
    * xhtml2pdf (`<http://www.xhtml2pdf.com/>`_)
    * pillow (`<https://github.com/python-pillow/Pillow>`_)

    
    
 .. _design-goal:
 
Design goal
===============================================================

 .. image:: _static/target.png
    :alt: target image
    :align: center

 * Project management tool
 * Efficient data storage 
 * Sorting, analysis, aggregation and reporting of data
 * Data visualization
 * Improved data access
 * Automation of procedures
 * Facilitate communication

 .. _features:
   
Features
===============================================================
 * Multi-projects
 * Adding molecules by drawing or pasting SMILES code
 * Reading molecules from file (csv, smi, sdf, mol, txt)
 * Data presenting in sortable columns
 * Exporting data to file (file formats: xls, pdf, csv, sdf, txt, png)
 * PAINS (Pan Assay Interference Compounds) filtering (`DOI: 10.1021/jm901137j <http://pubs.acs.org/doi/abs/10.1021/jm901137j>`_)
 * History of changes
 * Compound filtering (by similarity, structure, identity, compound name, creator, adding date etc.)
 * Stars rating
 * IC50 determination based on least squares method, 
 * Automatic data processing
 * Graphs generation
 * Access managing
 * Tags
 
 .. _license:
 
License
===============================================================

This document is copyright (C) 2014 by Adrian Jasinski

This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to
Creative Commons, 543 Howard Street, 5th Floor, San Francisco, California, 94105, USA. 
