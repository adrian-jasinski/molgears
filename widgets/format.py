escape_dict={'\a':r'\a',
           '\b':r'\b',
           '\c':r'\c',
           '\f':r'\f',
           '\n':r'\n',
           '\r':r'\r',
           '\t':r'\t',
           '\v':r'\v',
           '\'':r'\'',
           '\"':r'\"',
           '\0':r'\0',
           '\1':r'\1',
           '\2':r'\2',
           '\3':r'\3',
           '\4':r'\4',
           '\5':r'\5',
           '\6':r'\6',
           '\7':r'\7',
           '\8':r'\8',
           '\9':r'\9'}

def raw(text):
    """Returns a raw string representation of text"""
    new_string=''
    for char in text:
        try: new_string+=escape_dict[char]
        except KeyError: new_string+=char
    return new_string
    
def raw_path_basename(path):
    """Returns basename from raw path string"""
    import ntpath
    path = raw(path)
    return ntpath.basename(path)

def kiformating(num):
    try:
        ki = float(num)
    except Exception:
        return u"Float error"
    if ki >= 100.0:
        return u">99.9"
    elif ki <100.0 and ki >=10.0:
        return "{:.1f}".format(ki)
    elif ki <10.0 and ki >= 1.0:
        return "{:.2f}".format(ki)
    elif ki <1.0 and ki >= 0.01:
        return "{:.3f}".format(ki)
    elif ki == 0.0:
        return "0.0"
    else:
        num = "{:.4f}".format(ki)
        return "%s.%s" %(num[1:5], num[-1])
