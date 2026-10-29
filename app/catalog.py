"""Research leads, not promises of active offers. No secrets or claimed rewards."""
CATALOG = [
 {'id':'github-student','title':'GitHub Education','kind':'Student benefits','description':'Explore developer tools for eligible students. Current benefits and verification requirements must be checked with GitHub.','url':'https://github.com/education','evidence_url':'https://docs.github.com/en/education/about-github-education/github-education-for-students/apply-to-github-education-as-a-student','evidence':'Official documentation describes student verification and an application review.','tags':['coding','developer','student','ai','tools'],'sample':True,'student':True,'countries':[],'automation':'unknown','deadline':None},
 {'id':'free-developer','title':'Free developer resources','kind':'Free tiers','description':'A community-maintained directory of developer infrastructure and software with free tiers. Each provider requires separate verification.','url':'https://free-for.dev','evidence_url':'https://github.com/ripienaar/free-for-dev','evidence':'The directory documents free tiers and excludes free trials from its scope.','tags':['coding','developer','cloud','ai','hosting','credits'],'sample':True,'student':False,'countries':[],'automation':'unknown','deadline':None},
 {'id':'hn-discovery','title':'Developer announcements','kind':'Discovery source','description':'Find public product announcements. Community posts are leads, not verified offers.','url':'https://news.ycombinator.com/show','evidence_url':'https://github.com/HackerNews/API','evidence':'The public API provides stories and items; it does not validate offers.','tags':['startup','hackathon','developer','ai','giveaway'],'sample':True,'student':False,'countries':[],'automation':'unknown','deadline':None},
]

def search(query):
    terms=set(query.lower().split())
    ranked=[(len(terms & set((item['title']+' '+item['description']+' '+' '.join(item['tags'])).lower().split())),item) for item in CATALOG]
    return [item for score,item in sorted(ranked,key=lambda pair:pair[0],reverse=True) if score or not terms]
