# project-specific filters for jinja2 templating
import markdown
from markupsafe import Markup

def markdownify(md):
    return markdown.markdown(md)

def percent(value):
    return f"{value*100:.1f}%"

def format_bp(bp):
    "Pretty-print bp information."
    bp = float(bp)
    if bp < 500:
        return f"{bp:.0f} bp"
    elif bp <= 500e3:
        return f"{round(bp / 1e3, 1):.1f} kbp"
    elif bp < 500e6:
        return f"{round(bp / 1e6, 1):.1f} Mbp"
    elif bp < 500e9:
        return f"{round(bp / 1e9, 1):.1f} Gbp"
    return f"??? {bp}"

def unique_weighted_bp(item):
    return format_bp(item['n_unique_weighted_found'] * item['scaled'])

def unique_flat_bp(item):
    return format_bp(item['unique_intersect_bp'])

def subsearch_link(item, search_db):
    nextlevel_name = search_db.get_nextlevel_db(item['match_name'])
    descr = item['match_description']
    #print(f"subsearch_link: for {item['match_name']} found {nextlevel_name}")
    if nextlevel_name:
        return Markup(f"<a href='./subsearch/{nextlevel_name}/'>{descr}</a>")
    else:
        return descr
    

filters_dict = {}
filters_dict['markdownify'] = markdownify
filters_dict['percent'] = percent
filters_dict['format_bp'] = format_bp
filters_dict['unique_weighted_bp'] = unique_weighted_bp
filters_dict['unique_flat_bp'] = unique_flat_bp
filters_dict['subsearch_link'] = subsearch_link

def add_filters(env_d):
    for k, v in filters_dict.items():
        env_d[k] = v
