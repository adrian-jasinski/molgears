# -*- coding: utf-8 -*-
from sqlalchemy.orm import relationship, relation
from sqlalchemy import Table, ForeignKey, Column, case
from sqlalchemy.types import Integer, Unicode, PickleType, DateTime, Text, Float, Boolean

from molgears.model import DeclarativeBase, metadata

from razi.orm import ChemColumn
from razi.chemtypes import Molecule, BitFingerprint
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property

#__all__ = [ 'Compound']

projects_table = Table('compounds_projects', metadata,
                              Column('gid', Integer, ForeignKey('compounds.gid'), primary_key = True),
                              Column('id', Integer, ForeignKey('projects.id'), primary_key = True))
                              
tags_table = Table('compounds_tags', metadata,
                              Column('gid', Integer, ForeignKey('compounds.gid'), primary_key = True),
                              Column('id', Integer, ForeignKey('tags.id'), primary_key = True))

sfiles_table = Table('sfiles', metadata,
                              Column('id', Integer, ForeignKey('scompounds.id'), primary_key = True),
                              Column('files_id', Integer, ForeignKey('files.files_id'), primary_key = True))

effort_files_table = Table('efiles', metadata,
                              Column('id', Integer, ForeignKey('efforts.id'), primary_key = True),
                              Column('files_id', Integer, ForeignKey('files.files_id'), primary_key = True))

sfiles_purity_table = Table('sfiles_purity', metadata,
                              Column('id', Integer, ForeignKey('spurity.id'), primary_key = True),
                              Column('files_id', Integer, ForeignKey('files.files_id'), primary_key = True))

lfiles_purity_table = Table('lfiles_purity', metadata,
                              Column('id', Integer, ForeignKey('lpurity.id'), primary_key = True),
                              Column('files_id', Integer, ForeignKey('files.files_id'), primary_key = True))


##ZWIAZEK: 
class ProjectTests(DeclarativeBase):
    __tablename__ = "projecttests"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    name = Column(Unicode)
    cell_line = Column(PickleType)

class Projects(DeclarativeBase):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)
    description = Column(Text)
    date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    tests = relationship("ProjectTests", backref="projects", order_by="ProjectTests.id")


class Tags(DeclarativeBase):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)

class Names(DeclarativeBase):
    __tablename__="names"
    id = Column(Integer, primary_key=True)
    compound_id = Column(Integer, ForeignKey('compounds.gid'))
    name = Column(Unicode)

class History(DeclarativeBase):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    compound_id = Column(Integer, ForeignKey('compounds.gid'))
    project = Column(Unicode)
    user = Column(Unicode)
    date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status = Column(Unicode)
    changes = Column(Text)

class CompoundsFiles(DeclarativeBase):
    __tablename__= "compoundsfiles"
    id = Column(Integer, primary_key=True)
    gid = Column(Integer, ForeignKey('compounds.gid'))
    name = Column(Unicode)
    filename = Column(Unicode)

class NameGroups(DeclarativeBase):
    """ Group for naming automatization.
        naming example (precision=4):
            - {prefix}_000{next}_{sufix}
        naming example (precision=3,next=24):
            - {prefix}_024_{sufix}
    """
    __tablename__ = "namegroups"
    id = Column(Integer, primary_key=True)
    prefix = Column(Unicode)
    sufix = Column(Unicode)
    next = Column(Integer)          # next number value
    precision = Column(Integer)     # number of zeros

class Compound(DeclarativeBase):
    __tablename__ = 'compounds'
    gid = Column(Integer, primary_key=True)
    seq = Column(Integer)
    project = relation(Projects, secondary=projects_table)
    name = Column(Unicode)
    inchi = Column(Unicode)
    structure = ChemColumn(Molecule)
#    atompair = ChemColumn(BitFingerprint)
#    torsion = ChemColumn(BitFingerprint)
    morgan = ChemColumn(BitFingerprint)
    author = Column(Unicode)

    mw = Column(Integer)
    logp = Column(Float)
    num_atoms = Column(Integer)
    num_hvy_atoms = Column(Integer)
    num_rings = Column(Integer)
    hba = Column(Integer)
    hbd = Column(Integer)
    tpsa = Column(Integer)
    qed = Column(Float)
    logs = Column(Float)
    isomer = Column(Boolean, unique=False, default=False)
    notes = Column(Text)

# liczba związków w tabelach 1,2,3:
    pnum = Column(Integer)
    snum = Column(Integer)
    lnum = Column(Integer)
    create_date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    creator = Column(Unicode) #osoba dodająca związek

    tags = relation(Tags, secondary=tags_table)
    names = relationship("Names")
    history = relationship("History")
    pains1_id =  Column(Integer, ForeignKey('pains1.id'))
    pains1 = relationship("PAINS1")
    pains2_id =  Column(Integer, ForeignKey('pains2.id'))
    pains2 = relationship("PAINS2")
    pains3_id =  Column(Integer, ForeignKey('pains3.id'))
    pains3 = relationship("PAINS3")
    group_id = Column(Integer, ForeignKey('namegroups.id'))
    group = relationship("NameGroups", backref="compounds")
    files = relationship("CompoundsFiles", backref="compounds")

    def __init__(self, name, structure, creator):
        self.name = name
        self.structure = structure
#        self.atompair = self.structure.atompair_b()
#        self.torsion = self.structure.torsion_b()
        self.morgan = self.structure.morgan_b(2)
        self.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.creator = creator
        self.mw = self.structure.mw.label('mw')
        self.logp = self.structure.logp.label('logp')
        self.num_atoms = self.structure.num_atoms.label('num_atmos')
        self.num_hvy_atoms = self.structure.num_hvy_atoms.label('num_hvy_atoms')
        self.num_rings = self.structure.num_rings.label('num_rings')
        self.hba = self.structure.hba.label('hba')
        self.hbd = self.structure.hbd.label('hbd')
        self.tpsa = self.structure.tpsa.label('tpsa')
    def __repr__(self):
        return '%s %s %s' % (self.gid, self.name, self.structure)



#Requests
class PStatus(DeclarativeBase):
    __tablename__="pstatus"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)
    #pcompounds_id = Column(Integer, ForeignKey('pcompounds.id'))

class PHistory(DeclarativeBase):
    __tablename__ = 'phistory'
    id = Column(Integer, primary_key=True)
    pcompound_id = Column(Integer, ForeignKey('pcompounds.id'))
    gid = Column(Integer)
    project = Column(Unicode)
    user = Column(Unicode)
    date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status = Column(Unicode)
    changes = Column(Text)

class PCompound(DeclarativeBase):
    __tablename__ = 'pcompounds'

    id = Column(Integer, primary_key=True)
    gid = Column(Integer, ForeignKey('compounds.gid'))
    seq = Column(Integer)
    priority = Column(Integer)

    mol = relationship("Compound", backref="pcompounds", order_by="Compound.gid")
    owner = Column(Unicode)
    principal = Column(Unicode) #zleceniodawca / recipient
#    lso = Column(Unicode)
    notes = Column(Text)
    create_date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status_id = Column(Integer, ForeignKey('pstatus.id'))
    status = relationship("PStatus")
    history = relationship("PHistory")

    def __init__(self):
        self.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self):
        return '%s %s' % (self.id, self.gid)

#synthesis:

class SFiles(DeclarativeBase):
    __tablename__= "files"
    files_id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    filename = Column(Unicode)
    description = Column(Text)

class LContentFiles(DeclarativeBase):
    __tablename__= "lcontentfiles"
    id = Column(Integer, primary_key=True)
    lcontent_id = Column(Integer, ForeignKey('lcontent.id'))
    name = Column(Unicode)
    filename = Column(Unicode)

class SStatus(DeclarativeBase):
    __tablename__="sstatus"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True)

class SHistory(DeclarativeBase):
    __tablename__ = 'shistory'
    id = Column(Integer, primary_key=True)
    scompound_id = Column(Integer, ForeignKey('scompounds.id'))
    gid = Column(Integer)
    project = Column(Unicode)
    user = Column(Unicode)
    date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status = Column(Unicode)
    changes = Column(Text)

class SPurity(DeclarativeBase):
    __tablename__ = 'spurity'

    id = Column(Integer, primary_key=True)
    lcompound_id = Column(Integer, ForeignKey('scompounds.id'))
    value = Column(Float)
    type = Column(Unicode)
    retention_time = Column(Float)
    filename = relation(SFiles, secondary=sfiles_purity_table)

    def __repr__(self):
        return '%s' % (self.value)

class Efforts(DeclarativeBase):
    __tablename__ = "efforts"
    id = Column(Integer, primary_key=True)
    scompound_id = Column(Integer, ForeignKey('scompounds.id'))
    name = Column(Unicode)
    reaction = relation(SFiles, secondary=effort_files_table)
    etap = Column(Integer)
    etap_max = Column(Integer)
    notes = Column(Text)


class SCompound(DeclarativeBase):
    __tablename__ = 'scompounds'

    id = Column(Integer, primary_key=True)
    seq = Column(Integer)                               #kolejność/ sekwencja
    pid = Column(Integer)                               # PCompound id
    gid = Column(Integer, ForeignKey('compounds.gid')) #Compound gid
    mol = relationship("Compound", backref="scompounds", order_by="Compound.gid")
    priority = Column(Integer)
    owner = Column(Unicode)
    principal = Column(Unicode) #zleceniodawca / recipient
    lso = Column(Unicode)
    notes = Column(Text)
    filename = relation(SFiles, secondary=sfiles_table)
    create_date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    stat1_date = Column(DateTime) #pending
    stat2_date = Column(DateTime) # synthesis
    stat3_date = Column(DateTime) # finished
    stat4_date = Column(DateTime) #received
    form = Column(Text)
    state = Column(Float)  #stan
    diff_date = Column(Integer)  # czas w tygodniach kiedy związek osiągnął date stat2_date = datetime.now()-SCompound.stat2_date

    status_id = Column(Integer, ForeignKey('sstatus.id'))
    status = relationship("SStatus")
    history = relationship("SHistory")
    purity = relationship("SPurity")
    effort = relationship("Efforts")
    effort_default = Column(Integer)
    etap_diff = Column(Integer)

    def __init__(self):
        self.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self):
        return '%s %s %s' % (self.id, self.pid, self.gid)

#LIBRARY
class LHistory(DeclarativeBase):
    __tablename__ = 'lhistory'
    id = Column(Integer, primary_key=True)
    lcompound_id = Column(Integer, ForeignKey('lcompounds.id'))
    gid = Column(Integer)
    project = Column(Unicode)
    user = Column(Unicode)
    date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status = Column(Unicode)
    changes = Column(Text)

class LPurity(DeclarativeBase):
    __tablename__ = 'lpurity'

    id = Column(Integer, primary_key=True)
    lcompound_id = Column(Integer, ForeignKey('lcompounds.id'))
    value = Column(Float)
    type = Column(Unicode)
    filename = relation(SFiles, secondary=lfiles_purity_table)

    def __repr__(self):
        return '%s' % (self.value)
    #Library -> Ctoxicity
class TestCT(DeclarativeBase):
    __tablename__ = 'testct'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    time = Column(Float)
    type = Column(Unicode)
    notes = Column(Text)
    project = Column(Unicode)

class CTFiles(DeclarativeBase):
    """
    Table for storing result files for Ctoxicity
    """
    __tablename__= "ctfiles"
    files_id = Column(Integer, primary_key=True)
    ctfiles_id = Column(Integer, ForeignKey('ctresults.id'))
    name = Column(Unicode)
    filename = Column(Unicode)

class CTHistory(DeclarativeBase):
    """
    History module for ctresults
    """
    __tablename__ = 'cthistory'
    id = Column(Integer, primary_key=True)
    ct_id = Column(Integer, ForeignKey('ctresults.id'))
    gid = Column(Integer)
    lid = Column(Integer)
    project = Column(Unicode)
    user = Column(Unicode)
    date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status = Column(Unicode)
    changes = Column(Text)

class CTResults(DeclarativeBase):
    """
    Ctoxicity results for compound in library (LCompound relationship)
    """
    __tablename__ = 'ctresults'
    id = Column(Integer, primary_key=True)
    gid = Column(Integer)
    lid = Column(Integer, ForeignKey('lcompounds.id'))
    date = Column(DateTime)
    ic50 = Column(Float)
    hillslope = Column(Float)
    r2 = Column(Float)
    cell_line = Column(Unicode)
    test = relationship('TestCT')
    test_id = Column(Integer, ForeignKey('testct.id'))
    history = relationship("CTHistory", backref="ctresults")
    files = relationship("CTFiles")
    notes = Column(Text)
    active = Column(Boolean, unique=False, default=True)                                    #Set result as active - True/False
    create_date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class LContent(DeclarativeBase):
    __tablename__ = 'lcontent'
    id = Column(Integer, primary_key=True)
    gid = Column(Integer)
    lid = Column(Integer, ForeignKey('lcompounds.id'))
    value = Column(Float)
    files = relationship("LContentFiles", backref="lcontent")

class MinusState(DeclarativeBase):
    __tablename__ = 'minusstate'
    id = Column(Integer, primary_key=True)
    lid = Column(Integer, ForeignKey('lcompounds.id'))
    create_date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    value = Column(Float)

class LCompound(DeclarativeBase):
    __tablename__ = 'lcompounds' 

    id = Column(Integer, primary_key=True)
    nr = Column(Integer)
    _avg_ct = Column(Float)
    seq = Column(Integer)
    gid = Column(Integer, ForeignKey('compounds.gid'))
    sid = Column(Integer) # SYNTHESIS ID or 0 - no synthesis record
    mol = relationship("Compound", backref="lcompounds")
    ctoxicity = relationship("CTResults", backref="lcompounds")

    content = relationship("LContent", uselist=False, backref="lcompounds") # zawartość
    owner = Column(Unicode)
    lso = Column(Unicode)
    form = Column(Text)
    synthesisvalue = Column(Float)  #ilość syntezy.
    state = Column(Float)  #stan mag.
    minusstate = relationship("MinusState", backref="lcompounds")
    box = Column(Unicode) #pudlo
    entry = Column(Unicode) #pozycja
    source = Column(Unicode) #zrodlo
    notes = Column(Text) #uwagi
    create_date = Column(DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    showme = Column(Boolean)            # True or False - show object in activity
    history = relationship("LHistory")
    purity = relationship("LPurity")

    def __init__(self):
        self.create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self):
        return '%s %s %s' % (self.id, self.sid, self.gid)


    @hybrid_property
    def lcode(self):
        if self.box and self.entry:
            return self.box+self.entry
        else:
            return ""

    @lcode.expression
    def lcode(cls):
        return case([
            (cls.box != None, cls.box + cls.entry),
        ], else_ = None)

    # ----------------- avg ct ----------    
    @hybrid_property
    def avg_ct(self):
        return self._avg_ct

    @avg_ct.setter
    def avg_ct(self, cell_line):
        from collections import Iterable
        from sqlalchemy.sql.expression import null
        if self.ctoxicity:
            if isinstance(self.ctoxicity, Iterable):
                values = [ct.ic50 for ct in self.ctoxicity if ct.cell_line == cell_line and ct.active]
            else:
                values = null()
            try:
                self._avg_ct = round(sum(values)/len(values), 4)
            except ZeroDivisionError:
                self._avg_ct = null() # the default value
        else:
            self._avg_ct = null()

    @hybrid_method
    def average_ct(self, cell_line):
        '''average ic50 of ctoxicity for selected cell line'''
        from numpy import array
        from collections import Iterable
        if self.ctoxicity:
            if isinstance(self.ctoxicity, Iterable):
                values = [ct.ic50 for ct in self.ctoxicity if ct.cell_line == cell_line and ct.active]
            else:
                values = [0]
        else:
            return (0, 0)
        nums =  array(values)
        Yerr = nums.std()
        try:
            res = round(sum(values)/len(values), 4)
            return (res, round(Yerr, 2))
        except ZeroDivisionError:
            return (0, 0) # the default value

class PAINS1(DeclarativeBase):
##p_l15.txt
    __tablename__ = 'pains1'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    structure = Column(Unicode)

    def __init__(self, name, structure):
        self.name = name
        self.structure = structure
    def __repr__(self):
        return '%s %s %s' % (self.id, self.name, self.structure)

class PAINS2(DeclarativeBase):
##p_l150.txt
    __tablename__ = 'pains2'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    structure = Column(Unicode)

    def __init__(self, name, structure):
        self.name = name
        self.structure = structure
    def __repr__(self):
        return '%s %s %s' % (self.id, self.name, self.structure)

class PAINS3(DeclarativeBase):
##p_m150.txt
    __tablename__ = 'pains3'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    structure = Column(Unicode)

    def __init__(self, name, structure):
        self.name = name
        self.structure = structure
    def __repr__(self):
        return '%s %s %s' % (self.id, self.name, self.structure)


