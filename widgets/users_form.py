#TABLEBASE:
#from sprox.dojo.tablebase import DojoTableBase as TableBase
#from sprox.dojo.fillerbase import DojoTableFiller as TableFiller
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.dojo.formbase import DojoAddRecordForm, DojoEditableForm
from sprox.dojo.fillerbase import DojoTableFiller
from sprox.fillerbase import EditFormFiller

from tg import expose, flash, tmpl_context, redirect, request, url
from tg.decorators import paginate, with_trailing_slash
from tw2.forms import TextField, TextArea, FileField
from chemdb.model import DBSession, metadata, PCompound, PHistory, PStatus, Tags, SCompound, SStatus, SFiles, SHistory, SPurity, LCompound, LPurity
from tgext.crud.utils import get_table_headers, SortableTableBase
import transaction, genshi, os
from sqlalchemy import desc, asc
from chemdb.widgets.structure import create_image, addsmi, checksmi

# %%%%%%%%%%%%%% projektowanie %%%%%%%%%%%%%%%%%%%%%%

class NewPCompoundForm(DojoAddRecordForm):
    __model__ = PCompound
    
    
    __omit_fields__ = ['id', 'tags_id', 'atompair', 'torsion', 'morgan' , 'create_date', 'status_date', 'status', 'owner', 'mw', 'logp', 'history', 'hba', 'hbd', 'num_atoms', 'tpsa',
    ] 
    __field_attrs__ = {'structure':{'size':'59'}, 'name':{'rows':'1', 'cols':'80'}}
    __field_order__ = ['name', 'structure', 'tags']
    __require_fields__ = ['name', 'structure']
    #__field_widget_args__ = {'structure':{'help_text':'Add structure in SMILES format.'}, 'name':{'help_text':'Enter molecule name.'}}
    #addtag = TextField('addtag', label_text='Add New Tag: ', help_text = 'Add new Tag and push submit button. Notice: This field should be empty for molecule adding.')
    #smiles_file = FileField('smiles_file', 
     #       label_text='Choose file:',
    #        help_text = 'Please provide a smi, mol or sdf file.')
    #deltags=SubmitButton('deltags', label_text='Delete Tags: ',  name='Delete', attrs={"value": "Delete tags", "name":"deltags", "class":"deltags"})
    
new_pcompound_form = NewPCompoundForm(DBSession)

class ReadFromFileForm(DojoAddRecordForm):
    from tw2.forms import FileField
    __model__ = PCompound
    __field_order__ = ['tags', 'notes']
    __omit_fields__ = [
    'id', 'tags_id', 'atompair', 'torsion', 'morgan' , 'create_date', 'status_date', 'status', 'owner', 'structure', 'name', 'mw', 'logp', 'history', 'hba', 'hbd', 'num_atoms', 'tpsa',
    ] 
    read_file = FileField('file', 
            label_text='Choose file:',
            help_text = 'Please provide a smi, mol or sdf file.')
read_from_file_form = ReadFromFileForm(DBSession)


class EditPCompoundForm(DojoEditableForm):
    __omit_fields__ = [
    'id', 'atompair', 'torsion', 'morgan' , 'create_date', 'status_date', 'owner', 'mw', 'logp', 'history', 'hba', 'hbd', 'num_atoms', 'tpsa','status'
    ]
    __field_attrs__ = {'structure':{'rows':'1', 'cols':'80'}, 'name':{'rows':'1', 'cols':'80'}}
    __field_widget_types__ = dict(name=TextField, structure=TextArea)
    __model__= PCompound
edit_pcompoud_form = EditPCompoundForm(DBSession)

class EditPCompoundTableFiller(EditFormFiller):
    __model__ = PCompound
edit_pcompoud_filler = EditPCompoundTableFiller(DBSession)

#class PCompoundDetailTableFiller( TableFiller):
#    __model__ = PCompound
#    
#    __add_fields__ = {'image':None}
#    __xml_fields__ = ['image']
#    def image(self, obj):
#        return genshi.Markup('<a class="thumbnail" href="#thumb"><img src="%s" width="120px" height="120px" border="0" /><span><img src="%s" /><br />[<b>%s</b>] %s</span></a>' %
#                                        (url("/p_images/" + "thumb" + str(obj.id) + ".png"), url("/p_images/" + str(obj.id) + ".png"), obj.id, obj.name)
#                                           )
#    
#    def __actions__(self, obj):
#        """Override this function to define how action links should be displayed for the given record."""
#        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
#        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
#        value = '<div><div>&nbsp;<a href="'+pklist+'/edit" style="text-decoration:none">edytuj</a>'\
#              '</div><div>'\
#              '<a href="accept/'+pklist+'" style="text-decoration:none">akceptuj</a>'\
#              '</div><div>&nbsp;<a href="'+pklist+'/edit" style="text-decoration:none">odrzuc</a>'\
#              '</div><div>'\
#              '<form method="POST" action="'+pklist+'" class="button-to">'\
#            '<input type="hidden" name="_method" value="DELETE" />'\
#            '<input onclick="return confirm(\'Delete object?\');" value="usun" type="submit" '\
#            'style="background-color: transparent; float:left; border:0; color: #FE2E64; display: inline; margin: 0; padding: 0;"/>'\
#        '</form>'\
#        '</div></div>'
#        return value
#        
#    def _do_get_provider_count_and_objs(self, name=None, **kw):
#        userid = request.identity['repoze.who.userid']
#        
#        pcompound = DBSession.query(PCompound)
#        dsc = True
#        order = 'id'
#        if kw:
#            for k, v in kw.iteritems():
#                if str(k) == 'desc' and str(v) != '1':
#                    dsc = None
#                elif str(k) == 'order_by':
#                    order = v
##                else:
##                    scompound = scompound.filter(str(k)==str(v))
#        if dsc:
#            pcompound = pcompound.order_by(desc(order))
#        else:
#            pcompound = pcompound.order_by((order))
#        
#        pcompound = pcompound.all()
#        return len(pcompound), pcompound
#        
##    def _do_get_provider_count_and_objs(self, **kw):
##        limit = kw.pop('limit', None)
##        offset = kw.pop('offset', None)
##        order_by = kw.pop('order_by', 'id')
##        desc = kw.pop('desc', False)
##        count, objs = self.__provider__.query(self.__entity__, limit, offset, self.__limit_fields__, order_by, desc, filters=kw)
##        self.__count__ = count
##        return count, objs
#        
#pcompound_detail_filler = PCompoundDetailTableFiller(DBSession)


#class PCompoundDetailTable(TableBase):
#    __model__ = PCompound
#    __omit_fields__ = ['atompair', 'torsion', 'morgan', 'status_id', 'structure', 'status_date', 'history', 'notes']
#    __field_order__ = ['id', 'name', 'image', 'owner', 'create_date', 'status', 'status_date', 'tags', 'structure', 'notes', 'mw', 'logp', '__actions__']
#    __add_fields__ = {'image':None}
#    __xml_fields__ = ['Obraz', 'Akcja']
##    __column_widths__ = {'structure':"50px"}
#    __headers__ = {'name': 'Nazwa', 'structure':'Struktura', 'image':'Obraz', 
#                            'owner':'Wlasciciel', 'create_date':'Data utworzenia', 'status':'Status', 'tags':'Tagi', 'notes':'Uwagi' , '__actions__':'Akcja', 'mw':'MW', 'logp':'logP'}
#
#pcompound_detail_table = PCompoundDetailTable(DBSession)

# $$$$$$$$$$$$$$$$$$$$$ synthesis  $$$$$$$$$$$$$$$$$$$$$$$$$$$$

class SCompoundTableFiller( TableFiller):
    __model__ = SCompound
    
    __add_fields__ = {'image':None, 'pliki':None, 'czystosc':None}
    __xml_fields__ = ['image', 'pliki']
    def image(self, obj):
        return genshi.Markup('<a class="thumbnail" href="#thumb"><img src="%s" width="120px" height="120px" border="0" /><span><img src="%s" /><br />[<b>%s</b>] %s</span></a>' %
                                        (url("/s_images/" + "thumb" + str(obj.id) + ".png"), url("/s_images/" + str(obj.id) + ".png"), obj.id, obj.name)
                                           )

    def __actions__(self, obj):
        """Override this function to define how action links should be displayed for the given record."""
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'\
              '<a href="etap/'+pklist+'" style="text-decoration:none" onclick="return confirm(\'Change etap to next?\')">+etap</a>'\
              '<div>'\
              '<a href="details/'+pklist+'" style="text-decoration:none">szczegoly</a>'\
              '</div><div>'\
              '<a href="accept/'+pklist+'" style="text-decoration:none">akceptuj</a>'\
              '</div><div>&nbsp;<a href="'+pklist+'/edit" style="text-decoration:none">edytuj</a>'\
              '</div>'\
              '</div>'
        return value 
    
    def pliki(self, obj):
        import collections
        if obj.filename:
            if isinstance(obj.filename, collections.Iterable):
                value= '<div><ol>'
                for file in obj.filename:
                    value += '<li><a href="/files/{0}">{1}</a></li>'.format(file.filename, file.name)
#                    value += '{0},'.format(file.filename)
                value += '</ol></div>'
                return value
            else:
                return genshi.Markup('<a href="/files/{0}">test_{0}</a>'.format(obj.filename.filename) )
        else:
            return genshi.Markup('<em>None</em>')
            
    def czystosc(self, obj):
        purity_values = [p.value for p in obj.purity ]
        try:
            max_purity = max(purity_values)
        except Exception:
            max_purity = 'Brak danych'
            pass
#        index = purity_values.index(max_purity)
#        type = scompound.purity[index].type
        return max_purity

        
    def _do_get_provider_count_and_objs(self, name=None, **kw):
        userid = request.identity['repoze.who.userid']
        scompound = DBSession.query(SCompound).filter(SCompound.owner.contains(userid))
        dsc = True
        order = 'id'
        if kw:
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    order = v
#                else:
#                    scompound = scompound.filter(str(k)==str(v))
        if dsc:
            scompound = scompound.order_by(desc(order))
        else:
            scompound = scompound.order_by((order))
        
        scompound = scompound.all()
        return len(scompound), scompound
scompound_filler = SCompoundTableFiller(DBSession)

class SCompoundTable(TableBase):
    __model__ = SCompound
     
    __omit_fields__ = ['atompair', 'torsion', 'morgan', 'status_id', 'file_id', 'structure', 'status_date', 'filename', 'history', 'purity', 'notes', 'hba', 'hbd', 'num_atoms', 'tpsa','pliki', 'create_date', 'p_id']
    __field_order__ = ['id', 'p_id', 'name', 'image', 'owner', 'principal', 'create_date', 'status', 'status_date', 'tags', 'structure', 'etap_max', 'etap', 'lso', 'purity', 'pliki', 'notes', 'mw', 'logp', 'czystosc', '__actions__']
    __add_fields__ = {'image':None, 'pliki':None, 'czystosc':None}
    __xml_fields__ = ['Obraz', 'pliki', 'Akcja']
#    __column_widths__ = {'structure':"50px"}
    __headers__ = {'name': 'Nazwa', 'structure':'Struktura', 'image':'Obraz', 'purity':'Analityka', 'lso':'LSO', 'etap':'Ukonczony etap', 
                            'owner':'Wlasciciel', 'create_date':'Data utworzenia', 'status':'Status', 'tags':'Tagi', 'notes':'Uwagi' , 'etap_max':'Liczba etapow',
                            'filename':'Zalaczniki', '__actions__':'Akcja', 'mw':'MW', 'logp':'logP', 'principal':'odbiorca'}
scompound_table = SCompoundTable(DBSession)


class SCompoundSearchTableFiller( TableFiller):
    __model__ = SCompound
    
    __add_fields__ = {'image':None, 'pliki':None}
    __xml_fields__ = ['image', 'pliki']
    def image(self, obj):
        return genshi.Markup('<a class="thumbnail" href="#thumb"><img src="%s" width="120px" height="120px" border="0" /><span><img src="%s" /><br />[<b>%s</b>] %s</span></a>' %
                                        (url("/s_images/" + "thumb" + str(obj.id) + ".png"), url("/s_images/" + str(obj.id) + ".png"), obj.id, obj.name)
                                           )

    def __actions__(self, obj):
        """Override this function to define how action links should be displayed for the given record."""
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'\
              '<a href="etap/'+pklist+'" style="text-decoration:none" onclick="return confirm(\'Change etap to next?\')">+etap</a>'\
              '<div>&nbsp;<a href="'+pklist+'/edit" style="text-decoration:none">edytuj</a>'\
              '</div>'\
              '</div>'
        return value 
    
    def pliki(self, obj):
        import collections
        if obj.filename:
            if isinstance(obj.filename, collections.Iterable):
                value= '<div><ol>'
                for file in obj.filename:
                    value += '<li><a href="/files/{0}">{1}</a></li>'.format(file.filename, file.name)
                value += '</ol></div>'
                return value
            else:
                return genshi.Markup('<a href="/files/{0}">test_{0}</a>'.format(obj.filename.filename) )
        else:
            return genshi.Markup('<em>None</em>')

        
    def _do_get_provider_count_and_objs(self, name=None, **kw):
        userid = request.identity['repoze.who.userid']
        scompound = ()
        dsc = True
        order = 'id'
        if kw:
            try:
                smiles = kw['smi']
                method = kw['method']
            except Exception:
                smiles = None
                method = None
                pass
            try:
                ogranicz_tekst = kw['ogranicz_tekst']
            except Exception:
                ogranicz_tekst = None
                pass
            if smiles:
                if checksmi(smiles):
                    from razi.functions import functions
                    from razi.expression import TxtMoleculeElement
                    if method == 'smililarity':
                        query_bfp = functions.morgan_b(TxtMoleculeElement(smiles), 2)
                        constraint = SCompound.morgan.dice_similar(query_bfp)
                        dice_sml = SCompound.morgan.dice_similarity(query_bfp).label('dice')
        
    #                    scompound = DBSession.query(SCompound, dice_sml).filter(constraint).filter(SCompound.owner.contains(userid))
                        scompound = DBSession.query(SCompound).filter(constraint).filter(SCompound.owner.contains(userid))
                            
                    elif method == 'substructure':
                        constraint = SCompound.structure.contains(smiles)
                        scompound = DBSession.query(SCompound).filter(constraint).filter(SCompound.owner.contains(userid))
                    elif method == 'identity':
                        scompound = DBSession.query(SCompound).filter(SCompound.structure.equals(smiles)).filter(SCompound.owner.contains(userid))
#                    if ogranicz_tekst:
#                        scompound = scompound.filter(SCompound.__getattribute__(SCompound, kw['ogranicz']).like(ogranicz_tekst))
                else:
                    flash('SMILES error', 'warning')
                    scompound = ()
            else:
                scompound = DBSession.query(SCompound).filter(SCompound.owner.contains(userid))

            if ogranicz_tekst:
                if kw['ogranicz'] == 'p_id':
                    try:
                        p_id = int(ogranicz_tekst)
                        scompound = scompound.filter_by(p_id = p_id )
                    except Exception as msg:
                        flash('P_id should be a number: %s' % msg, 'error')
                else:
                    scompound = scompound.filter(SCompound.__getattribute__(SCompound, kw['ogranicz']).like(ogranicz_tekst))
            try:
                tagi = kw['tags']
            except Exception:
                tagi = None
                pass

            if isinstance(tagi, basestring):
                tagi_id = [int(tagi)]
            else:
                tagi_id = [int(id) for id in tagi]

            if tagi_id:
                import sqlalchemy
                scompound = scompound.filter(SCompound.tags.any(Tags.tags_id.in_(tagi_id)))
#            scompound = scompound.filter(SCompound.tags.contain(tagi_id))
#                scompound = scompound.join(SCompound.tags).filter_by(not_(tags_id = tagi_id[0]))

            if int(kw['status']) > 0:
                scompound = scompound.filter(SCompound.status_id == int(kw['status']))
                
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    order = v
            if scompound:
                if dsc:
                    scompound = scompound.order_by(desc(order))
                else:
                    scompound = scompound.order_by((order))
            
            scompound = scompound.all()
#        scompound = scompound.all()

        return len(scompound), scompound
scompound_search_filler = SCompoundSearchTableFiller(DBSession)

class SCompoundSearchTable(TableBase):
    __model__ = SCompound
     
    __omit_fields__ = ['atompair', 'torsion', 'morgan', 'status_id', 'file_id', 'structure', 'status_date', 'filename', 'history', 'hba', 'hbd', 'num_atoms', 'tpsa','pliki', 'create_date', 'purity']
    __field_order__ = ['id', 'p_id', 'name', 'image', 'owner', 'principal', 'create_date', 'status', 'status_date', 'tags', 'structure', 'etap_max', 'etap', 'lso', 'purity', 'pliki', 'notes', 'mw', 'logp', '__actions__']
    __add_fields__ = {'image':None, 'pliki':None}
    __xml_fields__ = ['Obraz', 'pliki', 'Akcja']
#    __column_widths__ = {'structure':"50px"}
    __headers__ = {'name': 'Nazwa', 'structure':'Struktura', 'image':'Obraz', 'purity':'Analityka', 'lso':'LSO', 'etap':'Ukonczony etap', 
                            'owner':'Wlasciciel', 'create_date':'Data utworzenia', 'status':'Status', 'tags':'Tagi', 'notes':'Uwagi' , 'etap_max':'Liczba etapow',
                            'filename':'Zalaczniki', '__actions__':'Akcja', 'mw':'MW', 'logp':'logP', 'principal':'odbiorca'}
scompound_search_table = SCompoundSearchTable(DBSession)

#class EditSCompoundForm(DojoEditableForm):
#    from tw.forms import FileField
#    __model__= SCompound
#    __omit_fields__ = ['id', 'atompair', 'torsion', 'morgan' , 'create_date', 'status_date', 'owner', 'etap', 'etap_max', 'filename', 'name',
#                                'structure', 'status', 'file_id', 'mw', 'logp', 'p_id', 'history', 'hba', 'hbd', 'num_atoms', 'tpsa','pliki', 'create_date',  'principal',
#    ]
##    __field_attrs__ = {'structure':{'rows':'1', 'cols':'80'}, 'name':{'rows':'1', 'cols':'80'}}
#    __field_widget_types__ = dict(name=TextField, structure=TextArea)
##    __add_fields__ = {'loadfile':None}
#    load_file = FileField('loadfile', 
#        label_text='Choose file:',
#        )
#edit_scompoud_form = EditSCompoundForm(DBSession)
#
#class EditSCompoundTableFiller(EditFormFiller):
#    __model__ = SCompound
#    __omit_fields__ = ['id', 'atompair', 'torsion', 'morgan' , 'create_date', 'status_date', 'owner', 'etap', 'etap_max', 'filename', 'name', 'structure',
#                                'status', 'file_id', 'mw', 'logp', 'p_id', 'history', 'hba', 'hbd', 'num_atoms', 'tpsa','pliki', 'create_date', 'principal', 
#    ]
#    #__add_fields__ = {'loadfile':None}
#edit_scompoud_filler = EditSCompoundTableFiller(DBSession)


#------------------@@@@@@@@@@@@@@@@@----------------


class LCompoundTableFiller( TableFiller):
    __model__ = LCompound
    
    __add_fields__ = {'image':None, 'czystosc':None}
    __xml_fields__ = ['image']
    def image(self, obj):
        return genshi.Markup('<a class="thumbnail" href="#thumb"><img src="%s" width="120px" height="120px" border="0" /><span><img src="%s" /><br />[<b>%s</b>] %s</span></a>' %
                                        (url("/l_images/" + "thumb" + str(obj.id) + ".png"), url("/l_images/" + str(obj.id) + ".png"), obj.id, obj.name)
                                           )

    def __actions__(self, obj):
        """Override this function to define how action links should be displayed for the given record."""
        primary_fields = self.__provider__.get_primary_fields(self.__entity__)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        value = '<div>'\
              '<div>'\
              '<a href="details/'+pklist+'" style="text-decoration:none">szczegoly</a>'\
              '</div>'\
              '<div>&nbsp;<a href="'+pklist+'/edit" style="text-decoration:none">edytuj</a>'\
              '</div>'\
              '</div>'
        return value

    def czystosc(self, obj):
        purity_values = [p.value for p in obj.purity ]
        try:
            max_purity = max(purity_values)
        except Exception:
            max_purity = 'Brak danych'
            pass
#        index = purity_values.index(max_purity)
#        type = scompound.purity[index].type
        return max_purity
        
    def _do_get_provider_count_and_objs(self, name=None, **kw):
        userid = request.identity['repoze.who.userid']
        lcompound = DBSession.query(LCompound)
        dsc = True
        order = 'id'
        if kw:
            for k, v in kw.iteritems():
                if str(k) == 'desc' and str(v) != '1':
                    dsc = None
                elif str(k) == 'order_by':
                    order = v
#                else:
#                    scompound = scompound.filter(str(k)==str(v))
        if dsc:
            lcompound = lcompound.order_by(desc(order))
        else:
            lcompound = lcompound.order_by((order))
        
        lcompound = lcompound.all()
        return len(lcompound), lcompound
lcompound_filler = LCompoundTableFiller(DBSession)

class LCompoundTable(TableBase):
    __model__ = LCompound
     
    __omit_fields__ = ['history', 'notes', 's_id', 'structure', 'atompair', 'torsion', 'morgan','purity']
    __field_order__ = ['id', 'name', 'image', 'create_date', 'tags', 'form', 'state', 'czystosc', 'box', 'entry', 'source', 'notes', '__actions__']
    __add_fields__ = {'image':None, 'czystosc':None}
    __xml_fields__ = ['Obraz', 'Akcja']
    __headers__ = {'image':'Obraz', 'notes':'Uwagi', '__actions__':'Akcja', 'create_date':'Data utworzenia', 'box':'Pudelko', 
                            'state':'Stan [mg]', 'form':'Forma', 'entry':'Pozycja', 'source':'zrodlo', 'name':'Nazwa', 'tags':'Tagi'}
lcompound_table = LCompoundTable(DBSession)
