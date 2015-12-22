import lxml.html

links = []

def func(args):
    result = args

    if not 'res_etree' in result:
        result['res_etree'] = lxml.html.fromstring(result['res_body'].decode('cp932',errors='ignore'))
    rt = result['res_etree']

    if len(links):
        links_et = rt.xpath('/html/body/div/div/div[@id="menu"]')[0]
        links_et[-1].tail = ' | '
        for link in links:
            links_et.append(link)
            if not links_et[-1].tail:
                links_et[-1].tail = ' | '


    return args
