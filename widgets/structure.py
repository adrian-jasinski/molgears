from rdkit.Chem import Draw,  MolFromSmiles, AllChem
import os

def create_image(id, structure, filepath, template=None):
    
    id = id
    mol = Chem.MolFromSmiles(str(structure))
    AllChem.EmbedMolecule(mol)
    # the molecule now has a crude conformation, clean it up:
#    AllChem.UFFOptimizeMolecule(mol)
    AllChem.Compute2DCoords(mol)
    if template:
        from rdkit.Chem.AllChem import GenerateDepictionMatching2DStructure
        temp = Chem.MolFromSmiles(str(template))
        AllChem.Compute2DCoords(temp)
        GenerateDepictionMatching2DStructure(mol,temp, acceptFailure=True)
    from rdkit.Chem.Draw.MolDrawing import MolDrawing
    MolDrawing.atomLabelFontSize=16
    Draw.MolToFile(mol, os.path.join(filepath,   str(id) + '.png'), size=(400, 400))
    MolDrawing.atomLabelFontSize=8
    Draw.MolToFile(mol, os.path.join(filepath,  'thumb' + str(id) + '.png'), size=(120, 120))
    
def create_reaction_image(rxn_path, image_path):
    from rdkit.Chem import rdChemReactions as Reactions
    react = Reactions.ReactionFromRxnFile(rxn_path)
    from rdkit.Chem.Draw import ReactionToImage
    image = ReactionToImage(react, subImgSize=(150, 150))
    image.save(image_path)

def checksmi(smiles):
    return MolFromSmiles(str(smiles))
    
from rdkit import Chem

def addsmi(filepath, limit=0):
    count = 1
    path = str(filepath)
    from rdkit.Chem import AllChem
    if str(path.split('.')[-1]) == 'sdf': #r 'mol'):
        suppl = Chem.SDMolSupplier(path)
        for mol in suppl:
            AllChem.EmbedMolecule(mol) # test
            AllChem.UFFOptimizeMolecule(mol) # test 
            AllChem.Compute2DCoords(mol) # test
            error = None
            if mol is None: continue
            smiles = str(Chem.MolToSmiles(Chem.RemoveHs(mol)))
            name = mol.GetProp('_Name')
            if not name:
                name = 'unknow_'
            if not smiles:
                continue
            if len(smiles) > 600: 
                error = smiles
                
            smiles = smiles.replace('=N#N','=[N+]=[N-]')
            smiles = smiles.replace('N#N=','[N-]=[N+]=')
            if not Chem.MolFromSmiles(smiles):
                error = smiles
            yield name,  smiles,  error, count
            
            if count == limit:
                break
            count += count
            
    else:    
        try:
            inputfile = open(filepath, 'rb')
        except Exception as msg:
            print msg

        for line in inputfile:
            error = None
            try:
                smiles, name = line.split()
            except Exception as msg:
                print msg
            if not name:
                name = 'unknow_' + inputfile.split('/')[-1]
            if not smiles:
                continue
            if len(smiles) > 600: 
                #name, smiles = None, None
                errors = smiles
                
            smiles = smiles.replace('=N#N','=[N+]=[N-]')
            smiles = smiles.replace('N#N=','[N-]=[N+]=')
            if not Chem.MolFromSmiles(smiles):
                errors = smiles
                
            yield name,  smiles,  error, count
    
            if count == limit:
                break
            count += count
