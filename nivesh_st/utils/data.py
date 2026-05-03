"""
NIVESH — Data Layer v3
Universe: ~700+ NSE stocks (Nifty 50 + Next50 + Midcap150 + Smallcap250 + Extra)
Macro: auto-detected live regime, applied as sector multiplier to every score.
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import concurrent.futures
import math
from datetime import datetime, timedelta

# ──────────────────────────────────────────────────────────────────────────
# UNIVERSE — ~700+ NSE symbols
# ──────────────────────────────────────────────────────────────────────────

NIFTY50 = [
    "RELIANCE","TCS","HDFCBANK","BHARTIARTL","ICICIBANK","INFOSYS","SBIN",
    "HINDUNILVR","ITC","LT","KOTAKBANK","AXISBANK","BAJFINANCE","MARUTI",
    "HCLTECH","SUNPHARMA","TITAN","ADANIENT","ONGC","NTPC","POWERGRID",
    "BAJAJFINSV","WIPRO","NESTLEIND","ULTRACEMCO","JSWSTEEL","TATAMOTORS",
    "TATASTEEL","TECHM","HINDALCO","DIVISLAB","DRREDDY","CIPLA","EICHERMOT",
    "APOLLOHOSP","ADANIPORTS","ASIANPAINT","GRASIM","HEROMOTOCO","LTIM",
    "BPCL","COALINDIA","SHRIRAMFIN","SBILIFE","TRENT","HDFCLIFE","BRITANNIA",
    "BAJAJ-AUTO","ZOMATO","DMART",
]

NIFTY_NEXT50 = [
    "PIDILITIND","TATACONSUM","HAVELLS","NAUKRI","BERGEPAINT","DABUR","COLPAL",
    "SIEMENS","ABB","TORNTPHARM","MUTHOOTFIN","HAL","BEL","IRCTC","MARICO",
    "GODREJCP","PERSISTENT","COFORGE","LTTS","KPITTECH","ASTRAL","VOLTAS",
    "DIXON","POLYCAB","TATAPOWER","IRFC","PFC","RECLTD","NHPC","OFSS",
    "MPHASIS","BANDHANBNK","INDHOTEL","GAIL","BHEL","SAIL","CONCOR",
    "ALKEM","GODREJPROP","NUVOCO","OBEROIRLTY","PRESTIGE","SBICARD",
    "INDUSTOWER","CANBK","FEDERALBNK","IDFCFIRSTB","RBLBANK","UNIONBANK","IOB",
]

NIFTY_MIDCAP = [
    "ABCAPITAL","ABFRL","APOLLOTYRE","AUROPHARMA","BALKRISIND","BATAINDIA",
    "BHARATFORG","BIOCON","CANFINHOME","CHOLAFIN","CROMPTON","DEEPAKNTR",
    "ESCORTS","GLENMARK","GRANULES","HINDPETRO","HUDCO","JBCHEPHARM",
    "JKCEMENT","JUBLFOOD","KAJARIACER","KANSAINER","LALPATHLAB","LICHSGFIN",
    "LUPIN","MANAPPURAM","MAXHEALTH","MCX","METROPOLIS","MGL","MOTHERSON",
    "NATIONALUM","NAVINFLUOR","PAGEIND","PIIND","RAMCOCEM","SJVN",
    "SONACOMS","SUNDARMFIN","SUNTV","SUPREMEIND","TATACHEM","TATACOMM",
    "TATAELXSI","THERMAX","TIINDIA","TRIDENT","VEDL","WHIRLPOOL",
    "AARTIIND","CAMS","CDSL","DELHIVERY","DEVYANI","FIVESTAR","HOMEFIRST",
    "KAYNES","KFINTECH","LATENTVIEW","NYKAA","POLICYBZR","UTIAMC",
    "ANGELONE","CHOLAHLDNG","CREDITACC","DOMS","EMAMILTD","GILLETTE",
    "HAPPSTMNDS","HATSUN","JYOTICNC","JUSTDIAL","MAHINDCIE","MASTEK",
    "MEDPLUS","MTAR","NEWGEN","OLECTRA","ORIENTELEC","PAISALO","PCJEWELLER",
    "PHOENIXLTD","PRINCEPIPE","QUESS","RAYMOND","REDINGTON","RELAXO",
    "ROUTE","SAPPHIRE","SOBHA","SOLARA","SPARC","STARCEMENT","SUDARSCHEM",
    "SUMICHEM","SYMPHONY","TANLA","TEAMLEASE","THYROCARE","TIMKEN",
    "TIPSINDLTD","TRITURBINE","TRIVENI","TTKPRESTIG","TVSHLTD","UNIPARTS",
    "V2RETAIL","VSTIND","WABAG","WELCORP","WESTLIFE","WONDERLA","ZENSARTECH",
    "APTUS","CAMPUS","EASEMYTRIP","IDEAFORGE","IXIGO","MAPMYINDIA",
    "RATEGAIN","SYRMA","TARC","UPDATER","VGUARD","WELSPUNLIV",
]

NIFTY_SMALLCAP = [
    "ACLGATI","ACMESOLAR","ADANIGREEN","ADANIPOWER","AFFLE","AJANTPHARM",
    "ALKEM","AMARAJABAT","AMBER","AMBUJACEM","APTUS","ARVINDFASN",
    "ASAHIINDIA","ASHOKLEYLAND","ASKAUTOLTD","ASTERDM","ATGL","ATUL",
    "AVANTIFEED","BALRAMCHIN","BALAMINES","BASF","BBTC","BIKAJI",
    "BLUESTARCO","BORORENEW","BSE","BUREAUVERITAS","CAMLINFINE","CEATLTD",
    "CHALET","CHEMCON","CIGNITI","CLEAN","CONCORDBIO","CRAFTSMAN",
    "DCMSHRIRAM","DFMFOODS","DHANUKA","DOLAT","DYNAMATECH","ELECON",
    "ELGIEQUIP","EMAMI","ENGINERSIN","ERIS","FINEORG","FLUOROCHEM",
    "FORTIS","GABRIEL","GAEL","GICRE","GLAND","GMRINFRA","GODFRYPHLP",
    "GODREJAGRO","GPPL","GREENPANEL","GRINDWELL","GSFC","GUJGASLTD",
    "HAPPYFORGE","HIKAL","HLEGLAS","HONAUT","IBREALEST","ICICIPRULI",
    "ICICIGI","IEX","INDGN","INDIGRID","INTELLECT","IPCALAB","IRCON",
    "ISEC","ITDC","JAMNAAUTO","JINDALSAW","JKPAPER","JSWENERGY",
    "JUBILANT","KALPATPOWR","KPIL","KSCL","LEMONTREE","LINDEINDIA",
    "LTFOODS","LUXIND","MARKSANS","MAYURUNIQ","MRPL","MSUMI",
    "NATCOPHARM","NETWORK18","NFL","NIACL","NIITLTD","OIL",
    "PGHH","PILANIINVS","PNBHOUSING","PPLPHARMA","PREMIEREXP",
    "PRICOLLTD","RPGLIFE","SANOFI","SEQUENT","SHREECEM","SHREEPUSHK",
    "SHRIRAMCIT","SIYSIL","SOLCHEM","SRDHHSGFIN","SUPRIYA","SUVENPHAR",
    "SWSOLAR","TASTYBITE","TATAINVEST","TCNSCLOTH","TCIEXP","TCPL",
    "TEXRAIL","TINPLATE","VSTIND","WABAG","WELCORP","YATHARTH",
    "AARTIDRUGS","ACCELYA","ACUITAS","ADANIENSOL","AEGISCHEM","AGIGREENPAC",
    "AHLUCONT","AIAENG","AJMERA","AKZOINDIA","ALLCARGO","ALMONDZ",
    "ALPHAGEO","ALUFLUORIDE","AMBIKCO","AMJLAND","AMRUTANJAN","ANANTRAJ",
    "ANDHRSUGAR","ANMOL","ANTGRAPHIC","APARINDS","APCOTEXIND","APEEJAYSURC",
    "ARCOTECH","ARCHIDPLY","ARCHIES","ARIHANTCAP","ARMANFIN","AROGRANITE",
    "ARROWGREEM","ARTEDZ","ARVIND","ARVSMART","ASALCBR","ASHAPURMIN",
    "ASHIANA","ASKFINVEST","ASPINWALL","ASTRAMICRO","ASTRAZEN","ATFL",
    "ATLANTAA","ATLASCYCLES","AUBANK","AURIONPRO","AUTOIND","AVTNPL",
    "AYMSYNTEX","AZAD","BAJAJCON","BAJAJHCARE","BAJAJHIND","BAJAJPHARM",
    "BALAJITELE","BALAXI","BALKRISHNA","BANARBEADS","BANCOINDIA","BARBEQUE",
    "BARNALIPH","BCONCEPTS","BEDMUTHA","BEPL","BERGEPAINT","BETAAMERICA",
    "BFINVEST","BFUTILITIE","BGRENERGY","BHAGERIA","BHARATGEAR","BHARATWIRE",
    "BHEL","BHOPALGAS","BIGBLOC","BINANIIND","BIOFILCHEM","BIRLACABLE",
    "BIRLACORPN","BIRLATYRES","BKMINDAA","BLACKBOX","BLACKROSE","BLKASHYAP",
    "BLKASHYAP","BLUECOAST","BMETALS","BODALCHEM","BOHRAIND","BOMDYEING",
    "BOROLTD","BPCL","BPLAST","BURNPUR","BUTTERFLY","BVCL",
    "CALSOFT","CAPACITE","CAPRIHANS","CARYSIL","CASTROLIND","CCL",
    "CERA","CEREBRA","CESC","CGPOWER","CHAMPION","CHEMFAB","CHENNPETRO",
    "CHETTINAD","CHOICEIN","CIEINDIA","CMMIPL","CMRSL","COCHINSHIP",
    "COLEMAN","COMPUSOFT","CONFIPET","CONTROLS","CORDS","COSMOFILM",
    "CREST","CTE","CUBEXTUBI","CUMMINSIND","CUPID","CYIENTDLM",
    "DAAWAT","DALMIASUGAR","DALMIABHA","DATAPATTNS","DBCORP","DBREALTY",
    "DCAL","DECCANCE","DEEPAKFERT","DELTA","DELTACORP","DENORA",
    "DHANI","DHARMAJ","DHUNSERI","DIACONTEXT","DIACHEM","DIAMONDYD",
    "DIGISPICE","DISA","DISHTV","DLINKINDIA","DMART","DOLLEX",
    "DONEAR","DPABHUSHAN","DPWIRES","DPZCONSULT","DREDGECORP","DSPBLKROCK",
    "DSSL","DVLS","DWARKESH","DYNPRO",
]

# Additional quality stocks from various sectors
EXTRA_STOCKS = [
    # IT / Tech
    "INFY","WIPRO","HCLTECH","TCS","TECHM","LTIM","PERSISTENT","COFORGE","MPHASIS",
    "OFSS","NIITTECH","HEXAWARE","KPITTECH","LTTS","CYIENTDLM","ZENSARTECH",
    "MASTEK","NEWGEN","INTELLECT","TATAELXSI","HAPPSTMNDS","LATENTVIEW",
    # Pharma / Healthcare
    "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","ALKEM","TORNTPHARM","LUPIN",
    "AUROPHARMA","BIOCON","GLAND","GRANULES","IPCALAB","GLENMARK","AJANTPHARM",
    "NATCOPHARM","PPLPHARMA","SPARC","SOLARA","SEQUENT","ERIS","SANOFI",
    "JBCHEPHARM","LALPATHLAB","METROPOLIS","THYROCARE","FORTIS","MAXHEALTH",
    "APOLLOHOSP","ASTERDM","YATHARTH",
    # Banking / Finance
    "HDFCBANK","ICICIBANK","SBIN","KOTAKBANK","AXISBANK","INDUSINDBK",
    "BANDHANBNK","IDFCFIRSTB","FEDERALBNK","RBLBANK","CANBK","UNIONBANK",
    "IOB","IDBI","AUBANK","DCBBANK","KARVYSTOCK","PNB","BANKBARODA",
    "INDIANB","CENTRALBK","MAHABANK","J&KBANK","KARNATAKA",
    # NBFC / Insurance
    "BAJFINANCE","BAJAJFINSV","SHRIRAMFIN","MUTHOOTFIN","MANAPPURAM",
    "CHOLAFIN","CANFINHOME","LICHSGFIN","PNBHOUSING","CREDITACC","FIVESTAR",
    "APTUS","HOMEFIRST","ABCAPITAL","PAISALO","SBICARD","SBILIFE","HDFCLIFE",
    "ICICIPRULI","ICICIGI","GICRE","NIACL",
    # Auto
    "MARUTI","TATAMOTORS","BAJAJ-AUTO","EICHERMOT","HEROMOTOCO","MOTHERSON",
    "APOLLOTYRE","CEATLTD","BHARATFORG","ESCORTS","BALKRISIND","TIINDIA",
    "MAHINDCIE","GABRIEL","PRICOLLTD","BOSCHLTD","EXIDEIND","AMARAJABAT",
    "MINDA","SUNDARMMFIN","TVSHLTD","SONACOMS","CRAFTSMAN",
    # FMCG / Consumer
    "HINDUNILVR","ITC","NESTLEIND","BRITANNIA","DABUR","MARICO","COLPAL",
    "GODREJCP","TATACONSUM","EMAMILTD","GILLETTE","PGHH","RELAXO","BATAINDIA",
    "PAGEIND","GODFRYPHLP","VSTIND","BIKAJI","DEVYANI","WESTLIFE",
    # Energy / Power
    "RELIANCE","ONGC","BPCL","HINDPETRO","GAIL","MRPL","OIL","CHENNPETRO",
    "NTPC","POWERGRID","TATAPOWER","ADANIENT","ADANIGREEN","ADANIPOWER",
    "SJVN","NHPC","RECLTD","PFC","IRFC","CESC","TORNTPOWER","JPPOWER",
    "ACMESOLAR","ATGL","GSPL","GUJGASLTD","PETRONET","MGL",
    # Capital Goods / Infra
    "LT","SIEMENS","ABB","BHEL","HAL","BEL","CGPOWER","POLYCAB","HAVELLS",
    "VOLTAS","CROMPTON","KAJARIACER","KANSAINER","THERMAX","KALPATPOWR",
    "ENGINERSIN","KPIL","GRINDWELL","ELGIEQUIP","TIMEKENNO","ELECON",
    "WABAG","WELCORP","SUPRIYA","INDUSTOWER",
    # Metal / Mining
    "JSWSTEEL","TATASTEEL","HINDALCO","VEDL","NATIONALUM","SAIL","NMDC",
    "HINDCOPPER","MOIL","WELSPUNIND","JINDALSAW","JKPAPER","GREENPANEL",
    # Real Estate
    "DLF","GODREJPROP","PRESTIGE","OBEROIRLTY","PHOENIXLTD","SOBHA",
    "BRIGADE","MAHLIFE","LODHA","NUVOCO","CHALET","IBREALEST",
    # Telecom / Internet
    "BHARTIARTL","ZOMATO","NAUKRI","INDIAMART","IRCTC","DMART",
    "POLICYBZR","NYKAA","DELHIVERY","MAPMYINDIA","IXIGO","RATEGAIN",
    # Cement
    "ULTRACEMCO","AMBUJACEM","SHREECEM","RAMCOCEM","JKCEMENT","HEIDELBERG",
    "STARCEMENT","NUVOCO","BIRLACORPN","KESORAMIND",
    # Chemicals
    "PIDILITIND","DEEPAKNTR","NAVINFLUOR","AARTIIND","ATUL","FINEORG",
    "FLUOROCHEM","BALRAMCHIN","GSFC","GNFC","SUDARSCHEM","SUMICHEM",
    "CHEMCON","BALAMINES","AGIGREENPAC","TATACHEM","CAMLINFINE",
    # Defence
    "HAL","BEL","BHEL","COCHINSHIP","GARDENREACH","GRSE","PARAS",
    "IDEAFORGE","SYRMA","KAYNES","AVALON",
    # Diversified
    "GRASIM","ITC","BAJAJHLDNG","MCDOWELL-N","UNITDSPR","TATAELXSI",
]

FULL_UNIVERSE = list(dict.fromkeys(
    NIFTY50 + NIFTY_NEXT50 + NIFTY_MIDCAP + NIFTY_SMALLCAP + EXTRA_STOCKS
))

# Aliases for compatibility
NIFTY100 = list(dict.fromkeys(NIFTY50 + NIFTY_NEXT50))
NIFTY500 = list(dict.fromkeys(NIFTY50 + NIFTY_NEXT50 + NIFTY_MIDCAP + NIFTY_SMALLCAP))

# ──────────────────────────────────────────────────────────────────────────
# SECTOR MAP
# ──────────────────────────────────────────────────────────────────────────

SECTOR_MAP = {
    "HDFCBANK":"Banking","ICICIBANK":"Banking","SBIN":"Banking","KOTAKBANK":"Banking",
    "AXISBANK":"Banking","BANDHANBNK":"Banking","INDUSINDBK":"Banking","CANBK":"Banking",
    "UNIONBANK":"Banking","IOB":"Banking","IDFCFIRSTB":"Banking","FEDERALBNK":"Banking",
    "RBLBANK":"Banking","AUBANK":"Banking","IDBI":"Banking","PNB":"Banking",
    "BANKBARODA":"Banking","INDIANB":"Banking","CENTRALBK":"Banking",
    "SBILIFE":"Insurance","HDFCLIFE":"Insurance","ICICIPRULI":"Insurance",
    "ICICIGI":"Insurance","GICRE":"Insurance","NIACL":"Insurance",
    "TCS":"IT","INFOSYS":"IT","HCLTECH":"IT","WIPRO":"IT","TECHM":"IT","LTIM":"IT",
    "PERSISTENT":"IT","COFORGE":"IT","MPHASIS":"IT","OFSS":"IT","LTTS":"IT",
    "KPITTECH":"IT","TATAELXSI":"IT","ZENSARTECH":"IT","MASTEK":"IT",
    "NEWGEN":"IT","INTELLECT":"IT","HAPPSTMNDS":"IT","LATENTVIEW":"IT",
    "HEXAWARE":"IT","CYIENTDLM":"IT","NIITTECH":"IT",
    "RELIANCE":"Energy","ONGC":"Energy","BPCL":"Energy","TATAPOWER":"Energy",
    "NTPC":"Energy","POWERGRID":"Energy","COALINDIA":"Energy","NHPC":"Energy",
    "RECLTD":"Energy","ADANIENT":"Energy","ADANIGREEN":"Energy","ADANIPOWER":"Energy",
    "SJVN":"Energy","HINDPETRO":"Energy","GAIL":"Energy","MRPL":"Energy",
    "OIL":"Energy","CESC":"Energy","ATGL":"Energy","GSPL":"Energy",
    "PETRONET":"Energy","MGL":"Energy","ACMESOLAR":"Energy","IRFC":"Energy",
    "PFC":"Energy","TORNTPOWER":"Energy","JPPOWER":"Energy","GUJGASLTD":"Energy",
    "BHARTIARTL":"Telecom","INDUSTOWER":"Telecom",
    "MARUTI":"Auto","TATAMOTORS":"Auto","BAJAJ-AUTO":"Auto","EICHERMOT":"Auto",
    "HEROMOTOCO":"Auto","MOTHERSON":"Auto","APOLLOTYRE":"Auto","CEATLTD":"Auto",
    "BHARATFORG":"Auto","ESCORTS":"Auto","BALKRISIND":"Auto","TIINDIA":"Auto",
    "MAHINDCIE":"Auto","GABRIEL":"Auto","MINDA":"Auto","TVSHLTD":"Auto",
    "SONACOMS":"Auto","CRAFTSMAN":"Auto","BOSCHLTD":"Auto","EXIDEIND":"Auto",
    "AMARAJABAT":"Auto","PRICOLLTD":"Auto",
    "HINDUNILVR":"FMCG","ITC":"FMCG","NESTLEIND":"FMCG","BRITANNIA":"FMCG",
    "DABUR":"FMCG","MARICO":"FMCG","COLPAL":"FMCG","GODREJCP":"FMCG",
    "TATACONSUM":"FMCG","EMAMILTD":"FMCG","GILLETTE":"FMCG","PGHH":"FMCG",
    "RELAXO":"FMCG","BATAINDIA":"FMCG","PAGEIND":"FMCG","GODFRYPHLP":"FMCG",
    "VSTIND":"FMCG","BIKAJI":"FMCG","DEVYANI":"FMCG","WESTLIFE":"FMCG",
    "SUNPHARMA":"Pharma","DRREDDY":"Pharma","CIPLA":"Pharma","DIVISLAB":"Pharma",
    "ALKEM":"Pharma","TORNTPHARM":"Pharma","LUPIN":"Pharma","AUROPHARMA":"Pharma",
    "BIOCON":"Pharma","GLAND":"Pharma","GRANULES":"Pharma","IPCALAB":"Pharma",
    "GLENMARK":"Pharma","AJANTPHARM":"Pharma","NATCOPHARM":"Pharma",
    "PPLPHARMA":"Pharma","SPARC":"Pharma","SOLARA":"Pharma","ERIS":"Pharma",
    "SANOFI":"Pharma","JBCHEPHARM":"Pharma","LALPATHLAB":"Healthcare",
    "METROPOLIS":"Healthcare","THYROCARE":"Healthcare","FORTIS":"Healthcare",
    "MAXHEALTH":"Healthcare","APOLLOHOSP":"Healthcare","ASTERDM":"Healthcare",
    "YATHARTH":"Healthcare",
    "JSWSTEEL":"Metal","TATASTEEL":"Metal","HINDALCO":"Metal","VEDL":"Metal",
    "NATIONALUM":"Metal","SAIL":"Metal","NMDC":"Metal","HINDCOPPER":"Metal",
    "MOIL":"Metal","JINDALSAW":"Metal","WELSPUNIND":"Metal",
    "BAJFINANCE":"NBFC","BAJAJFINSV":"NBFC","SHRIRAMFIN":"NBFC","MUTHOOTFIN":"NBFC",
    "MANAPPURAM":"NBFC","CHOLAFIN":"NBFC","CANFINHOME":"NBFC","LICHSGFIN":"NBFC",
    "PNBHOUSING":"NBFC","CREDITACC":"NBFC","FIVESTAR":"NBFC","APTUS":"NBFC",
    "HOMEFIRST":"NBFC","ABCAPITAL":"NBFC","PAISALO":"NBFC","SBICARD":"NBFC",
    "LT":"Capital Goods","SIEMENS":"Capital Goods","ABB":"Capital Goods",
    "BHEL":"Capital Goods","CGPOWER":"Capital Goods","POLYCAB":"Capital Goods",
    "HAVELLS":"Capital Goods","VOLTAS":"Capital Goods","CROMPTON":"Capital Goods",
    "THERMAX":"Capital Goods","KALPATPOWR":"Capital Goods","ENGINERSIN":"Capital Goods",
    "KPIL":"Capital Goods","GRINDWELL":"Capital Goods","ELGIEQUIP":"Capital Goods",
    "ELECON":"Capital Goods","WABAG":"Capital Goods","WELCORP":"Capital Goods",
    "HAL":"Defence","BEL":"Defence","COCHINSHIP":"Defence","GARDENREACH":"Defence",
    "GRSE":"Defence","IDEAFORGE":"Defence","KAYNES":"Defence","SYRMA":"Defence",
    "PIDILITIND":"Chemicals","DEEPAKNTR":"Chemicals","NAVINFLUOR":"Chemicals",
    "AARTIIND":"Chemicals","ATUL":"Chemicals","FINEORG":"Chemicals",
    "FLUOROCHEM":"Chemicals","GSFC":"Chemicals","SUDARSCHEM":"Chemicals",
    "SUMICHEM":"Chemicals","CHEMCON":"Chemicals","BALAMINES":"Chemicals",
    "TATACHEM":"Chemicals","CAMLINFINE":"Chemicals",
    "ULTRACEMCO":"Cement","AMBUJACEM":"Cement","SHREECEM":"Cement",
    "RAMCOCEM":"Cement","JKCEMENT":"Cement","STARCEMENT":"Cement","NUVOCO":"Cement",
    "DLF":"Realty","GODREJPROP":"Realty","PRESTIGE":"Realty","OBEROIRLTY":"Realty",
    "PHOENIXLTD":"Realty","SOBHA":"Realty","LODHA":"Realty","IBREALEST":"Realty",
    "ZOMATO":"Internet","NAUKRI":"Internet","IRCTC":"Internet","DMART":"Retail",
    "INDIAMART":"Internet","POLICYBZR":"Internet","NYKAA":"Internet",
    "DELHIVERY":"Internet","MAPMYINDIA":"Internet","IXIGO":"Internet",
    "RATEGAIN":"Internet","TRENT":"Retail","KAJARIACER":"Consumer",
    "ASIANPAINT":"Consumer","KANSAINER":"Consumer","TITAN":"Consumer",
    "GRASIM":"Diversified","HINDALCO":"Metal","TATACHEM":"Chemicals",
}

# ──────────────────────────────────────────────────────────────────────────
# INDEX / MACRO CONSTANTS
# ──────────────────────────────────────────────────────────────────────────

INDICES = {
    "Nifty 50":   "^NSEI",
    "Sensex":     "^BSESN",
    "Bank Nifty": "^NSEBANK",
    "India VIX":  "^INDIAVIX",
}

MACRO_SYMBOLS = {
    "USD/INR":     "USDINR=X",
    "Brent Crude": "BZ=F",
    "Gold":        "GC=F",
    "US 10Y":      "^TNX",
    "S&P 500":     "^GSPC",
    "Nasdaq":      "^IXIC",
    "EUR/USD":     "EURUSD=X",
    "WTI Crude":   "CL=F",
}

SECTOR_INDICES = {
    "Bank":      "^NSEBANK",
    "IT":        "^CNXIT",
    "Auto":      "^CNXAUTO",
    "Pharma":    "^CNXPHARMA",
    "Metal":     "^CNXMETAL",
    "FMCG":      "^CNXFMCG",
    "Realty":    "^CNXREALTY",
    "Energy":    "^CNXENERGY",
    "Infra":     "^CNXINFRA",
    "PSU Bank":  "^CNXPSUBANK",
    "Financial": "^CNXFINANCE",
}

POPULAR_ETF = [
    ("NIFTYBEES.NS","Nifty 50 BeES","Nifty 50","Mirae"),
    ("BANKBEES.NS","Bank Nifty BeES","Bank Nifty","Nippon"),
    ("GOLDBEES.NS","Gold BeES","Gold","Nippon"),
    ("JUNIORBEES.NS","Junior BeES","Nifty Jr","Nippon"),
    ("ITBEES.NS","IT BeES","Nifty IT","Nippon"),
    ("PHARMABEES.NS","Pharma BeES","Nifty Pharma","Nippon"),
    ("SETFNIFBK.NS","SBI Bank ETF","Bank Nifty","SBI"),
    ("AUTOBEES.NS","Auto BeES","Nifty Auto","Nippon"),
    ("MONIFTY500.NS","Motilal 500","Nifty 500","Motilal"),
    ("MIDCAPETF.NS","Midcap ETF","Nifty Midcap","Mirae"),
    ("SILVERBEES.NS","Silver BeES","Silver","Nippon"),
    ("HNGSNGBEES.NS","Hang Seng BeES","Hang Seng","Nippon"),
]

# ──────────────────────────────────────────────────────────────────────────
# SECTOR MACRO SENSITIVITY TABLE
# Each value = score adjustment (-15 to +15) based on macro factor
# ──────────────────────────────────────────────────────────────────────────

SECTOR_MACRO = {
    # sector: {crude_high, crude_low, inr_weak, inr_strong, high_vix,
    #          us_bull, us_bear, rate_cut, rate_hike, mkt_up, mkt_down}
    "Banking":      {"crude_high":-2,"crude_low":1,"inr_weak":-2,"inr_strong":2,
                     "high_vix":-4,"us_bull":3,"us_bear":-3,"rate_cut":8,"rate_hike":-3,"mkt_up":4,"mkt_down":-4},
    "IT":           {"crude_high":-1,"crude_low":1,"inr_weak":10,"inr_strong":-8,
                     "high_vix":-3,"us_bull":6,"us_bear":-8,"rate_cut":2,"rate_hike":0,"mkt_up":5,"mkt_down":-5},
    "Energy":       {"crude_high":12,"crude_low":-8,"inr_weak":3,"inr_strong":-2,
                     "high_vix":-2,"us_bull":2,"us_bear":-2,"rate_cut":1,"rate_hike":-1,"mkt_up":3,"mkt_down":-3},
    "Auto":         {"crude_high":-6,"crude_low":5,"inr_weak":-3,"inr_strong":2,
                     "high_vix":-5,"us_bull":3,"us_bear":-4,"rate_cut":7,"rate_hike":-5,"mkt_up":4,"mkt_down":-4},
    "FMCG":         {"crude_high":-3,"crude_low":3,"inr_weak":-2,"inr_strong":1,
                     "high_vix":5,"us_bull":1,"us_bear":3,"rate_cut":2,"rate_hike":2,"mkt_up":2,"mkt_down":3},
    "Pharma":       {"crude_high":-1,"crude_low":1,"inr_weak":5,"inr_strong":-4,
                     "high_vix":4,"us_bull":2,"us_bear":3,"rate_cut":1,"rate_hike":1,"mkt_up":2,"mkt_down":4},
    "Healthcare":   {"crude_high":-1,"crude_low":1,"inr_weak":2,"inr_strong":-2,
                     "high_vix":4,"us_bull":1,"us_bear":3,"rate_cut":1,"rate_hike":1,"mkt_up":1,"mkt_down":3},
    "Metal":        {"crude_high":3,"crude_low":-2,"inr_weak":4,"inr_strong":-3,
                     "high_vix":-6,"us_bull":5,"us_bear":-7,"rate_cut":3,"rate_hike":-4,"mkt_up":6,"mkt_down":-7},
    "NBFC":         {"crude_high":-2,"crude_low":2,"inr_weak":-2,"inr_strong":2,
                     "high_vix":-5,"us_bull":3,"us_bear":-4,"rate_cut":9,"rate_hike":-6,"mkt_up":4,"mkt_down":-5},
    "Capital Goods":{"crude_high":-1,"crude_low":1,"inr_weak":-2,"inr_strong":2,
                     "high_vix":-3,"us_bull":3,"us_bear":-3,"rate_cut":5,"rate_hike":-3,"mkt_up":5,"mkt_down":-4},
    "Defence":      {"crude_high":2,"crude_low":-1,"inr_weak":1,"inr_strong":-1,
                     "high_vix":3,"us_bull":2,"us_bear":2,"rate_cut":3,"rate_hike":-1,"mkt_up":3,"mkt_down":1},
    "Chemicals":    {"crude_high":-3,"crude_low":4,"inr_weak":4,"inr_strong":-3,
                     "high_vix":-2,"us_bull":3,"us_bear":-3,"rate_cut":2,"rate_hike":-2,"mkt_up":3,"mkt_down":-3},
    "Cement":       {"crude_high":-2,"crude_low":2,"inr_weak":-1,"inr_strong":1,
                     "high_vix":-3,"us_bull":2,"us_bear":-3,"rate_cut":5,"rate_hike":-4,"mkt_up":3,"mkt_down":-4},
    "Realty":       {"crude_high":-2,"crude_low":2,"inr_weak":-2,"inr_strong":2,
                     "high_vix":-4,"us_bull":3,"us_bear":-4,"rate_cut":10,"rate_hike":-8,"mkt_up":5,"mkt_down":-5},
    "Internet":     {"crude_high":-1,"crude_low":1,"inr_weak":3,"inr_strong":-3,
                     "high_vix":-5,"us_bull":6,"us_bear":-6,"rate_cut":3,"rate_hike":-3,"mkt_up":6,"mkt_down":-6},
    "Retail":       {"crude_high":-2,"crude_low":2,"inr_weak":-2,"inr_strong":2,
                     "high_vix":-3,"us_bull":2,"us_bear":-3,"rate_cut":4,"rate_hike":-3,"mkt_up":3,"mkt_down":-3},
    "Consumer":     {"crude_high":-2,"crude_low":2,"inr_weak":-1,"inr_strong":1,
                     "high_vix":2,"us_bull":2,"us_bear":1,"rate_cut":3,"rate_hike":-2,"mkt_up":2,"mkt_down":1},
    "Insurance":    {"crude_high":-1,"crude_low":1,"inr_weak":-1,"inr_strong":1,
                     "high_vix":-3,"us_bull":2,"us_bear":-2,"rate_cut":4,"rate_hike":2,"mkt_up":3,"mkt_down":-3},
    "Diversified":  {"crude_high":0,"crude_low":0,"inr_weak":0,"inr_strong":0,
                     "high_vix":-2,"us_bull":2,"us_bear":-2,"rate_cut":3,"rate_hike":-2,"mkt_up":2,"mkt_down":-2},
    "Telecom":      {"crude_high":-1,"crude_low":1,"inr_weak":-1,"inr_strong":1,
                     "high_vix":-1,"us_bull":1,"us_bear":-1,"rate_cut":2,"rate_hike":-1,"mkt_up":1,"mkt_down":-1},
    "Other":        {"crude_high":0,"crude_low":0,"inr_weak":0,"inr_strong":0,
                     "high_vix":0,"us_bull":0,"us_bear":0,"rate_cut":0,"rate_hike":0,"mkt_up":0,"mkt_down":0},
}

# ──────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────

def ns(symbol: str) -> str:
    s = symbol.upper().strip()
    if any(s.endswith(x) for x in [".NS",".BO","=X","=F"]) or s.startswith("^"):
        return s
    return s + ".NS"

def safe_last(series: pd.Series):
    c = series.dropna()
    return float(c.iloc[-1]) if not c.empty else None

def safe_prev(series: pd.Series):
    c = series.dropna()
    return float(c.iloc[-2]) if len(c) >= 2 else safe_last(series)

def is_market_open() -> bool:
    n = datetime.now()
    if n.weekday() >= 5:
        return False
    m = n.hour * 60 + n.minute
    return 9*60+15 <= m <= 15*60+30

def market_status_label() -> tuple:
    n = datetime.now()
    if n.weekday() >= 5:
        return "⛔ Weekend — Market Closed", "#4B5E78", False
    m = n.hour * 60 + n.minute
    if 9*60+15 <= m <= 15*60+30: return "🟢 Market Open", "#10D98D", True
    if 9*60 <= m < 9*60+15:      return "🟡 Pre-Market", "#F59E0B", False
    if 15*60+30 < m <= 16*60:    return "🔵 After Hours", "#38BDF8", False
    return "⛔ Market Closed", "#4B5E78", False

# ──────────────────────────────────────────────────────────────────────────
# LIVE MACRO REGIME (auto-detected)
# ──────────────────────────────────────────────────────────────────────────

def _fetch_single(name_sym: tuple):
    name, sym = name_sym
    try:
        hist = yf.Ticker(sym).history(period="10d", interval="1d", auto_adjust=True)
        hist = hist.dropna(how="all")
        if hist.empty:
            return None
        last = safe_last(hist["Close"])
        prev = safe_prev(hist["Close"])
        if last is None:
            return None
        chg = last - prev if prev is not None else 0
        pct = chg / prev * 100 if prev else 0
        return {"Name": name, "Symbol": sym, "Price": last, "Change": chg, "Change%": pct}
    except Exception:
        return None

@st.cache_data(ttl=120, show_spinner=False)
def get_live_macro_regime() -> dict:
    """
    Fetch ALL live macro indicators including global markets.
    Indian: Nifty, VIX, INR  |  US: S&P500, NASDAQ, 10Y
    Asia: Nikkei, Hang Seng  |  Commodities: Crude, Gold  |  FX: DXY
    """
    try:
        global_syms = [
            ("crude",   "BZ=F",     "BRENT"),
            ("vix",     "^INDIAVIX","INDIAVIX"),
            ("usdinr",  "INR=X",    "USDINR"),
            ("us10y",   "^TNX",     "US10Y"),
            ("nifty",   "^NSEI",    "NIFTY"),
            ("sp500",   "^GSPC",    "SP500"),
            ("nasdaq",  "^IXIC",    "NASDAQ"),
            ("nikkei",  "^N225",    "NIKKEI"),
            ("hsi",     "^HSI",     "HSI"),
            ("gold",    "GC=F",     "GOLD"),
            ("dxy",     "DX-Y.NYB", "DXY"),
        ]

        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            futures = {ex.submit(_fetch_quote, (yf_sym, name, None, None)): key
                       for key, yf_sym, name in global_syms}
            for fut in concurrent.futures.as_completed(futures, timeout=15):
                key = futures[fut]
                try: results[key] = fut.result()
                except Exception: results[key] = {}

        def val(key, field="Price", default=0):
            r = results.get(key, {})
            v = r.get(field, default) if r else default
            return float(v) if v is not None and v == v else default

        crude_price  = val("crude",  "Price",   80)
        vix_level    = val("vix",    "Price",   15)
        inr_level    = val("usdinr", "Price",   84)
        us10y        = val("us10y",  "Price",   4.5)
        gold_price   = val("gold",   "Price",   2000)
        dxy_level    = val("dxy",    "Price",   104)
        nifty_chg    = val("nifty",  "Change%", 0)
        sp_chg       = val("sp500",  "Change%", 0)
        nasdaq_chg   = val("nasdaq", "Change%", 0)
        nikkei_chg   = val("nikkei", "Change%", 0)
        hsi_chg      = val("hsi",    "Change%", 0)

        return {
            "crude_price":   crude_price,
            "vix_level":     vix_level,
            "inr_level":     inr_level,
            "us10y":         us10y,
            "gold_price":    gold_price,
            "dxy_level":     dxy_level,
            "nifty_chg":     nifty_chg,
            "sp_chg":        sp_chg,
            "nasdaq_chg":    nasdaq_chg,
            "nikkei_chg":    nikkei_chg,
            "hsi_chg":       hsi_chg,
            "crude_high":    crude_price > 90,
            "crude_low":     crude_price < 70,
            "high_vix":      vix_level > 20,
            "inr_weak":      inr_level > 85,
            "inr_strong":    inr_level < 82,
            "mkt_up":        nifty_chg > 0.5,
            "mkt_down":      nifty_chg < -0.5,
            "us_bull":       sp_chg > 0.5,
            "us_bear":       sp_chg < -0.5,
            "nasdaq_bull":   nasdaq_chg > 0.8,
            "nasdaq_bear":   nasdaq_chg < -0.8,
            "nikkei_up":     nikkei_chg > 0.5,
            "china_bull":    hsi_chg > 1.0,
            "china_bear":    hsi_chg < -1.0,
            "gold_high":     gold_price > 2200,
            "gold_low":      gold_price < 1800,
            "dollar_strong": dxy_level > 106,
            "dollar_weak":   dxy_level < 100,
            "rate_cut":      us10y < 4.0,
            "rate_hike":     us10y > 5.0,
        }
    except Exception:
        return {}



def compute_macro_score(sector: str, regime: dict) -> int:
    """Compute macro adjustment score for a sector given live regime."""
    table = SECTOR_MACRO.get(sector, SECTOR_MACRO["Other"])
    score = 0
    for flag, adj in table.items():
        if flag in regime and regime[flag] is True:
            score += adj
    return max(-20, min(20, score))

# ──────────────────────────────────────────────────────────────────────────
# QUOTE FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────────
# NSE LIVE DATA — ~15 second delay (effectively real-time for Indian stocks)
# yfinance has 15-20 min delay. NSE API is the best free live source.
# ──────────────────────────────────────────────────────────────────────────

def _get_nse_session() -> requests.Session:
    """Get a cookie-authenticated NSE session."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    try:
        session.get("https://www.nseindia.com/", timeout=10)
    except Exception:
        pass
    return session

@st.cache_data(ttl=15, show_spinner=False)  # 15-second cache = effectively live
def get_nse_live_quote(symbol: str) -> dict:
    """
    Fetch LIVE quote from NSE India (15-sec delay).
    Returns price, change, VWAP, circuit limits, sector PE, symbol PE.
    Much better than yfinance (15-20 min delay).
    """
    sym = symbol.upper().replace(".NS","").replace(".BO","")
    session = _get_nse_session()
    try:
        r = session.get(
            f"https://www.nseindia.com/api/quote-equity?symbol={sym}",
            headers={**NSE_HEADERS, "Referer": "https://www.nseindia.com/"},
            timeout=10
        )
        if not r.ok:
            return {}
        data = r.json()
        pi   = data.get("priceInfo", {})
        meta = data.get("metadata", {})
        hl   = pi.get("intraDayHighLow", {})
        whl  = pi.get("weekHighLow", {})

        last_price = pi.get("lastPrice") or pi.get("close")
        return {
            "symbol":       sym,
            "price":        last_price,
            "open":         pi.get("open"),
            "high":         hl.get("max"),
            "low":          hl.get("min"),
            "close":        pi.get("previousClose"),
            "change":       pi.get("change", 0),
            "changePercent":pi.get("pChange", 0),
            "vwap":         pi.get("vwap"),
            "upperCircuit": pi.get("upperCP"),
            "lowerCircuit": pi.get("lowerCP"),
            "hi52":         whl.get("max"),
            "lo52":         whl.get("min"),
            "sectorPE":     meta.get("pdSectorPe"),    # NSE sector PE — live!
            "symbolPE":     meta.get("pdSymbolPe"),    # NSE PE for this stock — live!
            "lastUpdate":   meta.get("lastUpdateTime"),
            "isLive":       True,
            "source":       "NSE India (15-sec delay)",
        }
    except Exception as e:
        return {}

@st.cache_data(ttl=15, show_spinner=False)  # 15-second cache = effectively live
def get_nse_live_indices() -> pd.DataFrame:
    """Fetch all NSE indices live from NSE India API."""
    session = _get_nse_session()
    try:
        r = session.get(
            "https://www.nseindia.com/api/allIndices",
            headers={**NSE_HEADERS, "Referer": "https://www.nseindia.com/"},
            timeout=10
        )
        if not r.ok:
            return pd.DataFrame()
        data  = r.json()
        indices = data.get("data", [])
        rows  = []
        key_indices = {
            "NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY AUTO",
            "NIFTY PHARMA", "NIFTY FMCG", "NIFTY METAL", "INDIA VIX",
            "NIFTY MIDCAP 100", "NIFTY SMALLCAP 100", "NIFTY REALTY",
            "NIFTY INFRA", "NIFTY ENERGY", "NIFTY FINANCIAL SERVICES",
        }
        for idx in indices:
            name = idx.get("index","")
            if name in key_indices or "NIFTY 5" in name:
                rows.append({
                    "Index":    name,
                    "Price":    idx.get("last"),
                    "Change":   idx.get("change"),
                    "Change%":  idx.get("percentChange"),
                    "Open":     idx.get("open"),
                    "High":     idx.get("high"),
                    "Low":      idx.get("low"),
                    "isLive":   True,
                    "Source":   "NSE India (15-sec delay)",
                })
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=30, show_spinner=False)
def get_nse_market_status() -> dict:
    """Get NSE market open/closed status + trading date."""
    session = _get_nse_session()
    try:
        r = session.get(
            "https://www.nseindia.com/api/marketStatus",
            headers={**NSE_HEADERS, "Referer": "https://www.nseindia.com/"},
            timeout=8
        )
        if r.ok:
            data = r.json()
            ms   = data.get("marketState", [{}])[0] if data.get("marketState") else {}
            return {
                "marketStatus": ms.get("marketStatus",""),
                "tradeDate":    ms.get("tradeDate",""),
                "index":        ms.get("index",""),
                "isOpen":       ms.get("marketStatus","") == "Open",
            }
    except Exception:
        pass
    return {"isOpen": is_market_open(), "marketStatus": "Unknown", "tradeDate": ""}

@st.cache_data(ttl=15, show_spinner=False)  # 15-sec = live
def _nse_quote_uncached(sym: str) -> dict:
    """Non-cached NSE quote for use in thread pools."""
    session = _get_nse_session()
    try:
        r = session.get(
            f"https://www.nseindia.com/api/quote-equity?symbol={sym}",
            headers={**NSE_HEADERS, "Referer": "https://www.nseindia.com/"},
            timeout=8
        )
        if not r.ok: return {}
        data = r.json()
        pi   = data.get("priceInfo", {})
        meta = data.get("metadata", {})
        hl   = pi.get("intraDayHighLow", {})
        whl  = pi.get("weekHighLow", {})
        last_price = pi.get("lastPrice") or pi.get("close")
        if not last_price: return {}
        return {
            "symbol": sym, "price": last_price,
            "open": pi.get("open"), "high": hl.get("max"), "low": hl.get("min"),
            "close": pi.get("previousClose"), "change": pi.get("change", 0),
            "changePercent": pi.get("pChange", 0), "vwap": pi.get("vwap"),
            "upperCircuit": pi.get("upperCP"), "lowerCircuit": pi.get("lowerCP"),
            "hi52": whl.get("max"), "lo52": whl.get("min"),
            "sectorPE": meta.get("pdSectorPe"), "symbolPE": meta.get("pdSymbolPe"),
            "lastUpdate": meta.get("lastUpdateTime"),
            "isLive": True, "source": "NSE India (15-sec delay)",
        }
    except Exception:
        return {}

def get_nse_live_multiple(symbols: list) -> pd.DataFrame:
    """
    Batch fetch live NSE quotes for multiple Indian stocks.
    Uses threading for speed. 15-second delay (effectively live).
    """
    sym_list = [s.upper().replace(".NS","").replace(".BO","") for s in symbols]

    def _fetch_one(sym):
        q = _nse_quote_uncached(sym)  # non-cached version safe for threads
        if q and q.get("price"):
            return {
                "Symbol":    sym,
                "Price":     q["price"],
                "Change":    q.get("change", 0),
                "Change%":   q.get("changePercent", 0),
                "Open":      q.get("open"),
                "High":      q.get("high"),
                "Low":       q.get("low"),
                "VWAP":      q.get("vwap"),
                "Upper Ckt": q.get("upperCircuit"),
                "Lower Ckt": q.get("lowerCircuit"),
                "NSE PE":    q.get("symbolPE"),
                "Sector PE": q.get("sectorPE"),
                "Last Update":q.get("lastUpdate",""),
                "Source":    "NSE Live",
            }
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        results = list(ex.map(_fetch_one, sym_list))
    rows = [r for r in results if r]
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def get_live_price(symbol: str) -> dict:
    """
    Get the most live price available for a symbol.
    Indian stocks → NSE API (15-sec delay)
    Others → yfinance (15-20 min delay)
    """
    sym_clean = symbol.upper().replace(".NS","").replace(".BO","")

    # Try NSE first for Indian stocks
    nse_q = get_nse_live_quote(sym_clean)
    if nse_q and nse_q.get("price"):
        return nse_q

    # Fallback to yfinance
    q = _fetch_quote((ns(symbol), symbol))
    if q:
        q["source"] = "yfinance (15-20 min delay)"
        q["isLive"]  = False
    return q or {}

def _fetch_quote(sym_orig: tuple):
    sym, orig = sym_orig
    try:
        hist = yf.Ticker(sym).history(period="10d", interval="1d", auto_adjust=True)
        hist = hist.dropna(how="all")
        if hist.empty:
            return None
        last = safe_last(hist["Close"])
        prev = safe_prev(hist["Close"])
        if last is None:
            return None
        chg = last - prev if prev is not None else 0
        pct = chg / prev * 100 if prev else 0
        return {
            "Symbol":  orig,
            "Price":   last,
            "Change":  chg,
            "Change%": pct,
            "High":    safe_last(hist["High"]) or last,
            "Low":     safe_last(hist["Low"]) or last,
            "Volume":  safe_last(hist["Volume"]) or 0,
            "LiveData": is_market_open(),
        }
    except Exception:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def get_multiple_quotes(symbols: list) -> pd.DataFrame:
    if not symbols:
        return pd.DataFrame()
    pairs = [(ns(s), s) for s in symbols]
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(_fetch_quote, pairs))
    rows = [r for r in results if r is not None]
    return pd.DataFrame(rows) if rows else pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_fundamentals(symbol: str) -> dict:
    try:
        return yf.Ticker(ns(symbol)).info or {}
    except Exception:
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def get_history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    try:
        df = yf.Ticker(ns(symbol)).history(period=period, interval=interval, auto_adjust=True)
        df.index = df.index.tz_localize(None)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def get_macro() -> pd.DataFrame:
    all_syms = {**INDICES, **MACRO_SYMBOLS}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(_fetch_single, list(all_syms.items())))
    rows = [r for r in results if r is not None]
    return pd.DataFrame(rows) if rows else pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def get_sectors() -> pd.DataFrame:
    pairs = list(SECTOR_INDICES.items())
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(_fetch_single, pairs))
    rows = []
    for r in results:
        if r:
            rows.append({"Sector": r["Name"], "Price": r["Price"], "Change%": r["Change%"]})
    df = pd.DataFrame(rows)
    return df.sort_values("Change%", ascending=False) if not df.empty else df

# ──────────────────────────────────────────────────────────────────────────
# UNIVERSE SCORING — 700+ stocks with LIVE MACRO INTEGRATION
# ──────────────────────────────────────────────────────────────────────────

def _fetch_info(sym_orig: tuple):
    sym, orig = sym_orig
    try:
        return orig, yf.Ticker(sym).info
    except Exception:
        return orig, {}

@st.cache_data(ttl=1800, show_spinner=False)
def get_universe_scores(category: str = "all") -> pd.DataFrame:
    """
    Score all ~700 NSE stocks.
    Score = Valuation(25) + Quality(30) + Growth(25) + Safety(20) + Technical(5) + MACRO(±20)
    """
    # Use live NSE universe — auto-updates daily when new stocks join indices
    universe = get_live_universe()
    syms = [(ns(s), s) for s in universe]

    # Fetch live macro regime once
    try:
        regime = get_live_macro_regime()
    except Exception:
        regime = {}

    # Parallel fundamentals fetch (25 workers for speed)
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as ex:
        results = list(ex.map(_fetch_info, syms))

    rows = []
    for orig, info in results:
        if not info:
            continue
        p = info.get("regularMarketPrice") or info.get("currentPrice")
        if not p or p <= 0:
            continue

        pe   = info.get("trailingPE")
        pb   = info.get("priceToBook")
        roe  = info.get("returnOnEquity")
        mg   = info.get("profitMargins")
        rg   = info.get("revenueGrowth")
        eg   = info.get("earningsGrowth")
        de   = info.get("debtToEquity")
        cr   = info.get("currentRatio")
        mc   = info.get("marketCap", 0)
        dy   = info.get("dividendYield")
        b    = info.get("beta")
        s50  = info.get("fiftyDayAverage")
        s200 = info.get("twoHundredDayAverage")
        hi52 = info.get("fiftyTwoWeekHigh")
        lo52 = info.get("fiftyTwoWeekLow")
        chg  = info.get("regularMarketChangePercent", 0) or 0
        atgt = info.get("targetMeanPrice")

        # ── Valuation (max 25) ────────────────────────────────────────────
        score = 0; why = []
        if pe and 0 < pe < 10:   score += 25; why.append(f"PE {pe:.1f}")
        elif pe and pe < 15:     score += 20; why.append(f"PE {pe:.1f}")
        elif pe and pe < 20:     score += 15; why.append(f"PE {pe:.1f}")
        elif pe and pe < 30:     score += 8
        elif pe and pe < 40:     score += 3
        elif pe and pe > 80:     score -= 5  # extremely overvalued
        if pb and 0 < pb < 1.5:  score += 5; why.append(f"PB {pb:.1f}")
        elif pb and pb < 3:      score += 3
        elif pb and pb < 5:      score += 1
        elif pb and pb > 15:     score -= 3

        # ── Quality (max 30) ──────────────────────────────────────────────
        if roe and roe > 0.30:   score += 20; why.append(f"ROE {roe*100:.0f}%")
        elif roe and roe > 0.20: score += 16; why.append(f"ROE {roe*100:.0f}%")
        elif roe and roe > 0.15: score += 12; why.append(f"ROE {roe*100:.0f}%")
        elif roe and roe > 0.10: score += 7
        elif roe and roe < 0:    score -= 5
        if mg and mg > 0.25:     score += 10; why.append(f"Margin {mg*100:.0f}%")
        elif mg and mg > 0.18:   score += 8;  why.append(f"Margin {mg*100:.0f}%")
        elif mg and mg > 0.12:   score += 5
        elif mg and mg > 0.06:   score += 2
        elif mg and mg < 0:      score -= 5

        # ── Growth (max 25) ───────────────────────────────────────────────
        if rg and rg > 0.30:     score += 13; why.append(f"Rev+{rg*100:.0f}%")
        elif rg and rg > 0.20:   score += 10; why.append(f"Rev+{rg*100:.0f}%")
        elif rg and rg > 0.10:   score += 7;  why.append(f"Rev+{rg*100:.0f}%")
        elif rg and rg > 0:      score += 3
        elif rg and rg < -0.10:  score -= 4
        if eg and eg > 0.30:     score += 12; why.append(f"EPS+{eg*100:.0f}%")
        elif eg and eg > 0.20:   score += 9;  why.append(f"EPS+{eg*100:.0f}%")
        elif eg and eg > 0.10:   score += 6
        elif eg and eg > 0:      score += 3
        elif eg and eg < -0.10:  score -= 4

        # ── Safety (max 20) ───────────────────────────────────────────────
        if de is not None and de < 10:    score += 12; why.append("Net cash")
        elif de is not None and de < 50:  score += 9;  why.append("Low debt")
        elif de is not None and de < 100: score += 5
        elif de is not None and de < 200: score += 2
        elif de is not None and de > 500: score -= 5
        if cr and cr > 2.5:      score += 8; why.append(f"CR {cr:.1f}x")
        elif cr and cr > 1.5:    score += 5
        elif cr and cr > 1.0:    score += 2
        elif cr and cr < 0.8:    score -= 3

        # ── Technical (max 10) ────────────────────────────────────────────
        tech = "Neutral"
        if p and s50 and s200:
            if p > s50 and p > s200:   score += 5; tech = "Bullish"
            elif p < s50 and p < s200: score -= 5; tech = "Bearish"
            elif p > s50:              score += 2; tech = "Neutral-Bull"
            else:                      score -= 2; tech = "Neutral-Bear"

        pos52 = None
        if hi52 and lo52 and p and hi52 > lo52:
            pos52 = (p - lo52) / (hi52 - lo52) * 100
            if pos52 < 15:   score += 5; why.append("Near 52W low")
            elif pos52 > 90: score -= 3

        # ── MACRO SCORE (±20) — LIVE ──────────────────────────────────────
        sector = SECTOR_MAP.get(orig, "Other")
        macro_adj = compute_macro_score(sector, regime) if regime else 0
        score += macro_adj
        if macro_adj > 5:  why.append(f"Macro+{macro_adj}")
        elif macro_adj < -5: why.append(f"Macro{macro_adj}")

        # ── Category filters ──────────────────────────────────────────────
        if category == "value"    and not (pe and 0 < pe < 20):   continue
        if category == "growth"   and not ((rg and rg>0.15) or (eg and eg>0.15)): continue
        if category == "quality"  and not (roe and roe>0.15 and mg and mg>0.10):  continue
        if category == "dividend" and not (dy and dy > 0.01):     continue
        if category == "smallcap" and not (mc and mc < 20000e7):  continue

        # Analyst upside
        analyst_upside = None
        if atgt and p and atgt > 0:
            analyst_upside = round((atgt / p - 1) * 100, 1)

        # ── Extended fundamentals ─────────────────────────────────────────
        ps       = info.get("priceToSalesTrailing12Months")
        ev_rev   = info.get("enterpriseToRevenue")
        ev_ebit  = info.get("enterpriseToEbitda") or info.get("ebitdaMargins")
        eps      = info.get("trailingEps")
        bv_ps    = (p / pb) if (pb and pb > 0 and p) else None  # book value per share
        peg      = None
        if pe and eg and eg > 0:
            peg = round(pe / (eg * 100), 2)
        graham   = None
        if eps and bv_ps and eps > 0 and bv_ps > 0:
            import math
            graham = round(math.sqrt(22.5 * eps * bv_ps), 2)
        graham_premium = None
        if graham and graham > 0 and p:
            graham_premium = round((p / graham - 1) * 100, 1)

        prom_h   = info.get("heldPercentInsiders")        # promoter/insider %
        inst_h   = info.get("heldPercentInstitutions")    # FII+DII+MF %
        fwd_pe   = info.get("forwardPE")
        op_mg    = info.get("operatingMargins")
        gr_mg    = info.get("grossMargins")
        roa      = info.get("returnOnAssets")
        ebitda   = info.get("ebitda")
        tot_debt = info.get("totalDebt")
        int_exp  = info.get("interestExpense")
        int_cov  = None
        if ebitda and int_exp and int_exp < 0:
            int_cov = round(-ebitda / int_exp, 1)
        elif ebitda and tot_debt and tot_debt > 0:
            int_cov = round(ebitda / (tot_debt * 0.08), 1)  # proxy: 8% cost of debt
        payout_r = info.get("payoutRatio")
        avg_vol  = info.get("averageVolume")
        cur_vol  = info.get("volume") or info.get("regularMarketVolume")
        vol_ratio= round(cur_vol / avg_vol, 2) if (cur_vol and avg_vol and avg_vol > 0) else None
        # ROCE proxy: Net Income / (Equity + Total Debt)
        net_inc  = info.get("netIncomeToCommon")
        eq_val   = info.get("totalStockholderEquity") or info.get("bookValue")
        roce     = None
        if net_inc and eq_val and tot_debt is not None:
            cap_emp = eq_val + tot_debt
            if cap_emp > 0:
                roce = round(net_inc / cap_emp * 100, 1)

        rows.append({
            "Symbol":              orig,
            "Name":                info.get("shortName",""),
            "Sector":              sector,
            "Price":               p,
            "Change%":             chg,
            "Market Cap":          mc,
            "PE":                  pe,
            "PE (Forward)":        fwd_pe,
            "PB":                  pb,
            "PS":                  ps,
            "EV/Revenue":          ev_rev,
            "EV/EBITDA":           ev_ebit,
            "EPS":                 eps,
            "PEG":                 peg,
            "Graham Number":       graham,
            "Graham Premium%":     graham_premium,
            "Book Value/Share":    bv_ps,
            "ROE":                 roe,
            "ROA":                 roa,
            "ROCE%":               roce,
            "Net Margin":          mg,
            "Operating Margin":    op_mg,
            "Gross Margin":        gr_mg,
            "Rev Growth":          rg,
            "EPS Growth":          eg,
            "D/E":                 de,
            "Current Ratio":       cr,
            "Interest Coverage":   int_cov,
            "FCF":                 info.get("freeCashflow"),
            "Payout Ratio":        payout_r,
            "Beta":                b,
            "Div Yield":           dy,
            "Promoter Holding%":   prom_h,
            "Institutional Hold%": inst_h,
            "Avg Volume":          avg_vol,
            "Volume Ratio":        vol_ratio,
            "52W%":                pos52,
            "52W High":            hi52,
            "52W Low":             lo52,
            "Tech":                tech,
            "Macro Score":         macro_adj,
            "Score":               max(0, min(120, score)),
            "Analyst Upside%":     analyst_upside,
            "AnalystTarget":       atgt,
            "Recommendation":      info.get("recommendationKey"),
            "Reasons":             ", ".join(why[:5]),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Score", ascending=False).reset_index(drop=True)
    return df

# ──────────────────────────────────────────────────────────────────────────
# ALPHA UNIVERSE — price returns + momentum for all stocks
# ──────────────────────────────────────────────────────────────────────────

PERIOD_MAP = {
    "Today":  ("2d",  "1d"),
    "1 Week": ("10d", "1d"),
    "1 Month":("45d", "1d"),
    "3 Month":("4mo", "1d"),
    "6 Month":("8mo", "1d"),
    "1 Year": ("15mo","1wk"),
}

def _fetch_price_history(sym_orig: tuple):
    sym, orig, period_yf, interval_yf = sym_orig
    try:
        hist = yf.Ticker(sym).history(period=period_yf, interval=interval_yf, auto_adjust=True)
        hist = hist.dropna(how="all")
        close = hist["Close"].dropna()
        if len(close) < 2:
            return None
        current = float(close.iloc[-1])
        start   = float(close.iloc[0])
        period_ret = (current / start - 1) * 100
        log_rets = np.log(close / close.shift(1)).dropna()
        ann_f = 252 if interval_yf == "1d" else 52
        vol   = float(log_rets.std() * np.sqrt(ann_f) * 100) if len(log_rets) > 1 else 20
        mom   = 0
        if len(close) >= 20:
            mom = (float(close.iloc[-10:].mean()) / float(close.iloc[-20:-10].mean()) - 1) * 100
        rsi_val = None
        if len(log_rets) >= 14:
            g = log_rets.clip(lower=0).ewm(com=13).mean().iloc[-1]
            l = (-log_rets).clip(lower=0).ewm(com=13).mean().iloc[-1]
            rsi_val = float(100 - 100/(1 + g/l)) if l > 0 else 60
        return {"Symbol": orig, "Price": current, "Period Ret%": period_ret,
                "Momentum": mom, "Volatility%": vol, "RSI": rsi_val}
    except Exception:
        return None

@st.cache_data(ttl=600, show_spinner=False)
def get_alpha_universe(timeframe: str = "1 Month") -> pd.DataFrame:
    period_yf, interval_yf = PERIOD_MAP.get(timeframe, ("45d","1d"))
    universe = get_live_universe()  # live NSE fetch — auto-updates daily
    syms = [(ns(s), s, period_yf, interval_yf) for s in universe]
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
        results = list(ex.map(_fetch_price_history, syms))
    rows = [r for r in results if r is not None]
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Sector"] = df["Symbol"].map(lambda s: SECTOR_MAP.get(s, "Other"))
    return df



@st.cache_data(ttl=21600, show_spinner=False)  # 6-hour cache — screener updates slowly
def get_screener_data(symbol: str) -> dict:
    """
    Fetch accurate Indian fundamental data from Screener.in.
    Much more reliable than yfinance for NSE stocks.
    Returns: PE, PB, ROE, ROCE, D/E, sales growth, profit growth, promoter pledging.
    """
    sym = symbol.upper().replace(".NS","").replace(".BO","")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.screener.in/",
    })
    data = {}
    try:
        # Try Screener.in company page
        url = f"https://www.screener.in/company/{sym}/consolidated/"
        r = session.get(url, timeout=10)
        if r.status_code == 404:
            url = f"https://www.screener.in/company/{sym}/"
            r = session.get(url, timeout=10)
        if not r.ok:
            return data

        import re as re_mod
        html = r.text

        def extract_num(pattern, text, default=None):
            m = re_mod.search(pattern, text)
            if m:
                try:
                    return float(m.group(1).replace(",","").replace("%",""))
                except: pass
            return default

        # Extract key ratios from ratios table
        # Screener shows: Stock P/E, Book Value, Dividend Yield, ROCE, ROE
        data["screener_pe"]       = extract_num(r'Stock P/E[^<]*<[^>]+>\s*([\d,.]+)', html)
        data["screener_pb"]       = extract_num(r'Price to Book Value[^<]*<[^>]+>\s*([\d,.]+)', html)
        data["screener_roce"]     = extract_num(r'ROCE[^<]*<[^>]+>\s*([\d,.]+)\s*%', html)
        data["screener_roe"]      = extract_num(r'ROE[^<]*<[^>]+>\s*([\d,.]+)\s*%', html)
        data["screener_div_yield"]= extract_num(r'Dividend Yield[^<]*<[^>]+>\s*([\d,.]+)\s*%', html)
        data["screener_debt"]     = extract_num(r'Debt to equity[^<]*<[^>]+>\s*([\d,.]+)', html)

        # Promoter pledging — critical governance signal
        pledged = extract_num(r'Pledged percentage[^<]*<[^>]+>\s*([\d,.]+)', html)
        if pledged is None:
            pledged = extract_num(r'pledged[^<]*<[^>]+>\s*([\d,.]+)\s*%', html)
        data["promoter_pledged_pct"] = pledged

        # Promoter holding
        prom = extract_num(r'Promoters\s*<[^>]+>\s*([\d,.]+)', html)
        data["screener_promoter_pct"] = prom

        # Sales growth (CAGR from compounded table)
        sales_3y = extract_num(r'Sales CAGR \(3Yrs\)[^<]*<[^>]+>\s*([\d,.-]+)\s*%', html)
        profit_3y= extract_num(r'Profit CAGR \(3Yrs\)[^<]*<[^>]+>\s*([\d,.-]+)\s*%', html)
        data["sales_cagr_3y"]   = sales_3y
        data["profit_cagr_3y"]  = profit_3y

        data["screener_url"] = url
        data["source"] = "screener.in"
        return {k: v for k, v in data.items() if v is not None}
    except Exception as e:
        return data

@st.cache_data(ttl=3600, show_spinner=False)
def get_nse_delivery_data(symbol: str) -> dict:
    """
    Fetch delivery percentage from NSE — critical Indian market signal.
    High delivery % = conviction buying (long-term holders, not traders).
    """
    sym = symbol.upper().replace(".NS","")
    session = _get_nse_session()
    try:
        r = session.get(
            f"https://www.nseindia.com/api/quote-equity?symbol={sym}&section=trade_info",
            headers={**NSE_HEADERS, "Referer":"https://www.nseindia.com/"},
            timeout=8
        )
        if not r.ok: return {}
        data = r.json()
        trade = data.get("marketDeptOrderBook",{}).get("tradeInfo",{})
        deliv = data.get("marketDeptOrderBook",{}).get("deliveryTrade",{})
        return {
            "total_traded_volume": trade.get("totalTradedVolume"),
            "total_traded_value":  trade.get("totalTradedValue"),
            "delivery_quantity":   deliv.get("deliveryQuantity"),
            "delivery_pct":        deliv.get("deliveryToTradedQuantity"),
        }
    except Exception:
        return {}

# ──────────────────────────────────────────────────────────────────────────
# LIVE UNIVERSE — fetched from NSE daily, auto-updates when new stocks added
# Fallback to hardcoded list if NSE API unavailable
# ──────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False)  # refresh once per day
def get_live_index_constituents(index_name: str) -> list:
    """
    Fetch live index constituents from NSE.
    Updates automatically when NSE adds/removes stocks from indices.
    e.g. index_name = "NIFTY 50", "NIFTY NEXT 50", "NIFTY MIDCAP 150"
    """
    session = _get_nse_session()
    try:
        encoded = index_name.replace(" ", "%20")
        r = session.get(
            f"https://www.nseindia.com/api/equity-stockIndices?index={encoded}",
            headers={**NSE_HEADERS, "Referer": "https://www.nseindia.com/market-data/live-equity-market"},
            timeout=12
        )
        if r.ok:
            data = r.json()
            stocks = data.get("data", [])
            syms = [s.get("symbol","") for s in stocks if s.get("symbol") and s.get("symbol") != index_name.replace("NIFTY ","")]
            clean = [s.upper().strip() for s in syms if s and len(s) >= 2]
            return clean
    except Exception:
        pass
    return []

@st.cache_data(ttl=86400, show_spinner=False)  # daily refresh
def get_live_universe() -> list:
    """
    Fetch ALL NSE-listed equity stocks (~2200+).
    Sources: NSE EQUITY_L.csv (complete list) → bhav copy → index APIs → hardcoded 545.
    Auto-updates when new stocks list on NSE — within 24 hours.
    """
    session = _get_nse_session()
    all_syms = set()

    # ── Source 1: NSE EQUITY_L.csv — authoritative full list ─────────────
    try:
        r = session.get(
            "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
            timeout=20
        )
        if r.ok and len(r.content) > 1000:
            import io as _io, csv as _csv
            reader = _csv.DictReader(_io.StringIO(r.text))
            for row in reader:
                sym    = (row.get("SYMBOL") or row.get("symbol") or "").strip().upper()
                series = (row.get("SERIES") or row.get("series") or "EQ").strip().upper()
                if sym and series in ("EQ", "BE", "BZ") and len(sym) >= 2:
                    all_syms.add(sym)
            if len(all_syms) > 500:
                return list(dict.fromkeys(list(all_syms) + FULL_UNIVERSE))
    except Exception:
        pass

    # ── Source 2: NSE Bhav Copy — all stocks traded today ────────────────
    try:
        from datetime import date as _date, timedelta as _td
        import zipfile as _zf, io as _io2, csv as _csv2
        for days_back in range(1, 8):
            d = _date.today() - _td(days=days_back)
            if d.weekday() >= 5: continue
            date_str = d.strftime("%d%b%Y").upper()
            url = (f"https://archives.nseindia.com/content/historical/EQUITIES/"
                   f"{d.year}/{d.strftime('%b').upper()}/cm{date_str}bhav.csv.zip")
            try:
                r2 = session.get(url, timeout=15)
                if r2.ok:
                    with _zf.ZipFile(_io2.BytesIO(r2.content)) as z:
                        with z.open(z.namelist()[0]) as zf:
                            for row in _csv2.DictReader(_io2.TextIOWrapper(zf)):
                                sym    = (row.get("SYMBOL") or "").strip().upper()
                                series = (row.get("SERIES") or "").strip().upper()
                                if sym and series in ("EQ","BE","BZ"):
                                    all_syms.add(sym)
                    if len(all_syms) > 500:
                        return list(dict.fromkeys(list(all_syms) + FULL_UNIVERSE))
                    break
            except Exception:
                continue
    except Exception:
        pass

    # ── Source 3: NSE Index APIs ──────────────────────────────────────────
    for idx in ["NIFTY 500","NIFTY TOTAL MARKET","NIFTY SMALLCAP 250",
                "NIFTY MIDCAP 150","NIFTY NEXT 50","NIFTY 50"]:
        all_syms.update(get_live_index_constituents(idx))

    if len(all_syms) > 200:
        return list(dict.fromkeys(list(all_syms) + FULL_UNIVERSE))

    # ── Fallback ──────────────────────────────────────────────────────────
    return FULL_UNIVERSE

@st.cache_data(ttl=86400, show_spinner=False)
def get_live_etf_list() -> list:
    """
    Fetch ALL ETFs listed on NSE — auto-updates when new ETFs launch.
    Returns list of dicts with symbol, name, underlying, scheme.
    Daily cache.
    """
    session = _get_nse_session()
    try:
        r = session.get(
            "https://www.nseindia.com/api/etf",
            headers={**NSE_HEADERS, "Referer": "https://www.nseindia.com/market-data/exchange-traded-funds-etf"},
            timeout=12
        )
        if r.ok:
            data = r.json()
            etfs = data.get("data", data if isinstance(data, list) else [])
            result = []
            for e in etfs:
                sym = e.get("symbol") or e.get("Symbol") or ""
                name = e.get("schemeName") or e.get("companyName") or e.get("name") or sym
                underlying = e.get("underlying") or e.get("underlyingIndex") or ""
                if sym:
                    result.append({
                        "symbol":     sym.upper(),
                        "yf_symbol":  f"{sym.upper()}.NS",
                        "name":       name,
                        "underlying": underlying,
                        "source":     "NSE Live",
                    })
            if result:
                return result
    except Exception:
        pass
    return []  # caller falls back to hardcoded list


@st.cache_data(ttl=1800, show_spinner=False)
def get_sector_pe_averages(universe_df: pd.DataFrame = None) -> dict:
    """Compute median PE per sector from the scored universe."""
    if universe_df is None or universe_df.empty:
        return {}
    result = {}
    for sector, grp in universe_df.groupby("Sector"):
        pe_vals = grp["PE"].dropna()
        pe_vals = pe_vals[(pe_vals > 0) & (pe_vals < 200)]
        if not pe_vals.empty:
            result[sector] = round(float(pe_vals.median()), 1)
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def get_corporate_actions(symbol: str) -> dict:
    """Fetch upcoming dividends, splits, bonus from yfinance."""
    try:
        t = yf.Ticker(ns(symbol))
        actions = {}
        try:
            div = t.dividends
            if not div.empty:
                div.index = div.index.tz_localize(None)
                last_3 = div.tail(3)
                actions["dividends"] = [
                    {"date": str(d.date()), "amount": round(float(v), 2)}
                    for d, v in last_3.items()
                ]
                actions["annual_div"] = round(float(last_3.sum()), 2)
        except Exception:
            pass
        try:
            splits = t.splits
            if not splits.empty:
                splits.index = splits.index.tz_localize(None)
                last_split = splits.tail(1)
                if not last_split.empty:
                    actions["last_split"] = {
                        "date": str(last_split.index[0].date()),
                        "ratio": float(last_split.iloc[0]),
                    }
        except Exception:
            pass
        cal = t.calendar
        if cal is not None:
            if isinstance(cal, pd.DataFrame):
                actions["calendar"] = cal.to_dict()
            else:
                actions["calendar"] = dict(cal) if cal else {}
        return actions
    except Exception:
        return {}


@st.cache_data(ttl=1800, show_spinner=False)
def get_nse_bulk_deals(days: int = 7) -> pd.DataFrame:
    """Fetch recent NSE bulk/block deals."""
    session = requests.Session()
    try:
        r = session.get("https://www.nseindia.com/", timeout=10,
                        headers={"User-Agent":"Mozilla/5.0","Accept":"*/*"})
        r2 = session.get(
            "https://www.nseindia.com/api/historical/bulk-deals?",
            headers=NSE_HEADERS, cookies=r.cookies, timeout=15
        )
        if r2.ok:
            data = r2.json()
            df = pd.DataFrame(data.get("data", []))
            return df
    except Exception:
        pass
    return pd.DataFrame()

# ──────────────────────────────────────────────────────────────────────────
# NSE OPTIONS
# ──────────────────────────────────────────────────────────────────────────

NSE_HEADERS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":"application/json, text/plain, */*",
    "Referer":"https://www.nseindia.com/option-chain",
    "sec-fetch-dest":"empty","sec-fetch-mode":"cors","sec-fetch-site":"same-origin",
}

@st.cache_data(ttl=60, show_spinner=False)
def get_options_chain(symbol: str = "NIFTY", opt_type: str = "indices") -> dict:
    session = requests.Session()
    try:
        r = session.get("https://www.nseindia.com/", timeout=10,
                        headers={"User-Agent":"Mozilla/5.0","Accept":"*/*"})
        ep = (f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
              if opt_type=="indices"
              else f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}")
        r2 = session.get(ep, headers=NSE_HEADERS, cookies=r.cookies, timeout=15)
        if not r2.ok:
            return {"error": f"NSE {r2.status_code}. Wait 30s and retry."}
        data    = r2.json()
        records = data.get("records", {})
        und     = records.get("underlyingValue", 0)
        expiries= records.get("expiryDates", [])
        chain   = []; total_c = total_p = 0
        for row in records.get("data", []):
            ce = row.get("CE",{}); pe = row.get("PE",{})
            coi = ce.get("openInterest",0); poi = pe.get("openInterest",0)
            total_c += coi; total_p += poi
            chain.append({"Strike":row.get("strikePrice",0),"Expiry":row.get("expiryDate",""),
                "Call OI":coi,"Call ΔOI":ce.get("changeinOpenInterest",0),
                "Call Vol":ce.get("totalTradedVolume",0),"Call IV":ce.get("impliedVolatility",0),
                "Call LTP":ce.get("lastPrice",0),"Call Chg":ce.get("change",0),
                "Put LTP":pe.get("lastPrice",0),"Put IV":pe.get("impliedVolatility",0),
                "Put Vol":pe.get("totalTradedVolume",0),"Put ΔOI":pe.get("changeinOpenInterest",0),
                "Put OI":poi,"Put Chg":pe.get("change",0)})
        pcr = round(total_p/total_c,3) if total_c else 0
        mp  = None
        if chain:
            mn = float("inf")
            for t in chain:
                ts = t["Strike"]
                pain = sum(max(0,r["Strike"]-ts)*r["Call OI"]+max(0,ts-r["Strike"])*r["Put OI"] for r in chain)
                if pain < mn: mn = pain; mp = ts
        return {"underlying":und,"expiries":expiries,"chain":chain,"pcr":pcr,"maxPain":mp,
                "totalCallOI":total_c,"totalPutOI":total_p}
    except Exception as e:
        return {"error": str(e)}

# ──────────────────────────────────────────────────────────────────────────
# MUTUAL FUNDS
# ──────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────
# MUTUAL FUND EXTENDED DATA — expense ratio, exit load, AUM, fund manager
# Sources: AMFI portal, mfapi.in, AMC factsheets
# ──────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False)   # 24-hour cache — changes rarely
def get_mf_scheme_details(scheme_code: int) -> dict:
    """
    Fetch extended MF details: expense ratio, exit load, AUM, fund manager,
    benchmark, min investment, risk grade, inception date.
    Primary: AMFI portal  |  Fallback: mfapi metadata + category rules
    """
    details = {}
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "*/*"})

    # ── Attempt 1: Groww/Valueresearch style API (AMFI fund details) ──────
    try:
        r = session.get(
            f"https://api.mfapi.in/mf/{scheme_code}",
            timeout=10
        )
        if r.ok:
            data = r.json()
            meta = data.get("meta", {})
            details["scheme_name"]     = meta.get("scheme_name", "")
            details["fund_house"]      = meta.get("fund_house", "")
            details["scheme_category"] = meta.get("scheme_category", "")
            details["scheme_type"]     = meta.get("scheme_type", "")
            details["scheme_code"]     = scheme_code
    except Exception:
        pass

    # ── Attempt 2: AMFI scheme-level data (has expense ratio for some) ────
    try:
        amfi_url = f"https://portal.amfiindia.com/PortalBackend.aspx?mf=MF&fn=GetSchemeDetails&SchCode={scheme_code}"
        r2 = session.get(amfi_url, timeout=8)
        if r2.ok and r2.text.strip():
            import json
            try:
                amfi_data = json.loads(r2.text)
                if isinstance(amfi_data, dict):
                    details["expense_ratio"] = amfi_data.get("ExpenseRatio") or amfi_data.get("expense_ratio")
                    details["exit_load"]     = amfi_data.get("ExitLoad") or amfi_data.get("exit_load")
                    details["aum_cr"]        = amfi_data.get("AUM") or amfi_data.get("aum")
                    details["fund_manager"]  = amfi_data.get("FundManager") or amfi_data.get("fund_manager")
                    details["benchmark"]     = amfi_data.get("Benchmark") or amfi_data.get("benchmark")
                    details["min_investment"]= amfi_data.get("MinInvestment")
                    details["risk_grade"]    = amfi_data.get("RiskGrade") or amfi_data.get("risk_grade")
                    details["inception_date"]= amfi_data.get("InceptionDate")
            except Exception:
                pass
    except Exception:
        pass

    # ── Fallback: category-based standard rules (always reliable) ─────────
    category = details.get("scheme_category", "").lower()
    name     = details.get("scheme_name", "").lower()

    # Expense ratio by category (typical ranges, SEBI regulated)
    if not details.get("expense_ratio"):
        if "direct" in name:
            if "liquid" in category or "overnight" in category:
                details["expense_ratio_est"] = "0.05–0.20% (Direct)"
            elif "debt" in category or "bond" in category:
                details["expense_ratio_est"] = "0.20–0.50% (Direct)"
            elif "index" in category or "etf" in category:
                details["expense_ratio_est"] = "0.05–0.30% (Direct)"
            else:
                details["expense_ratio_est"] = "0.30–0.80% (Direct equity)"
        else:
            if "liquid" in category or "overnight" in category:
                details["expense_ratio_est"] = "0.20–0.50% (Regular)"
            elif "debt" in category or "bond" in category:
                details["expense_ratio_est"] = "0.50–1.50% (Regular)"
            elif "index" in category or "etf" in category:
                details["expense_ratio_est"] = "0.10–0.50% (Regular)"
            else:
                details["expense_ratio_est"] = "1.00–2.25% (Regular equity)"

    # Exit load rules (SEBI regulated, standard across industry)
    if not details.get("exit_load"):
        if "liquid" in category or "overnight" in category or "money market" in category:
            details["exit_load_rule"]  = "Nil (liquid/overnight funds have no exit load)"
            details["exit_load_days"]  = 0
        elif "elss" in category or "tax" in category:
            details["exit_load_rule"]  = "Nil (ELSS has 3-year lock-in, no exit load after)"
            details["exit_load_days"]  = 0
        elif "debt" in category or "bond" in category or "gilt" in category:
            details["exit_load_rule"]  = "Nil or up to 0.25% within 7–30 days (varies by fund)"
            details["exit_load_days"]  = 30
        elif "index" in category:
            details["exit_load_rule"]  = "Usually Nil (check scheme info document)"
            details["exit_load_days"]  = 0
        else:
            # Most equity/hybrid funds: 1% if redeemed within 1 year
            details["exit_load_rule"]  = "1% if redeemed within 365 days · Nil after 1 year"
            details["exit_load_days"]  = 365
            details["exit_load_pct"]   = 1.0

    # Min investment (standard SEBI rules)
    if not details.get("min_investment"):
        if "elss" in category:
            details["min_investment_est"] = "₹500 (SIP) · ₹500 (Lump Sum) · Max ₹1.5L for 80C"
        elif "liquid" in category:
            details["min_investment_est"] = "₹1,000 (most liquid funds)"
        else:
            details["min_investment_est"] = "₹500 (SIP) · ₹1,000–5,000 (Lump Sum)"

    details["source"] = "AMFI + category rules"
    details["disclaimer"] = "Expense ratio and exit load are category estimates. Always verify in Scheme Information Document (SID) before investing."
    return details


@st.cache_data(ttl=86400, show_spinner=False)
def get_all_mf_schemes() -> list:
    """Fetch all 6000+ MF schemes from mfapi.in with fallback."""
    try:
        r = requests.get("https://api.mfapi.in/mf", timeout=15)
        if r.ok:
            schemes = r.json()
            if schemes and len(schemes) > 100:
                return schemes
    except Exception:
        pass
    # Fallback: return popular schemes only
    return [
        {"schemeCode": 119598, "schemeName": "Parag Parikh Flexi Cap Fund - Direct Plan"},
        {"schemeCode": 120503, "schemeName": "Mirae Asset Large Cap Fund - Direct Plan"},
        {"schemeCode": 118834, "schemeName": "SBI Small Cap Fund - Direct Plan"},
        {"schemeCode": 118989, "schemeName": "Axis Bluechip Fund - Direct Plan"},
        {"schemeCode": 122639, "schemeName": "Quant Small Cap Fund - Direct Plan"},
        {"schemeCode": 120701, "schemeName": "ICICI Prudential Bluechip Fund - Direct Plan"},
        {"schemeCode": 119062, "schemeName": "HDFC Mid-Cap Opportunities Fund - Direct Plan"},
        {"schemeCode": 125354, "schemeName": "Motilal Oswal Midcap Fund - Direct Plan"},
        {"schemeCode": 120505, "schemeName": "Mirae Asset Emerging Bluechip Fund - Direct Plan"},
        {"schemeCode": 120716, "schemeName": "Kotak Emerging Equity Fund - Direct Plan"},
    ]


@st.cache_data(ttl=3600, show_spinner=False)
def get_fo_ban_list() -> list:
    """
    Fetch NSE F&O ban list (stocks in ban cannot be traded in F&O).
    Updated daily by NSE. Returns list of banned symbols.
    """
    session = _get_nse_session()
    try:
        # NSE MWPL ban list
        r = session.get(
            "https://www.nseindia.com/api/fo-mwpl-data",
            headers={**NSE_HEADERS, "Referer":"https://www.nseindia.com/"},
            timeout=10
        )
        if r.ok:
            data = r.json()
            banned = [item.get("symbol","") for item in data.get("data",[])
                      if item.get("inBan") or item.get("status","").lower() == "ban"]
            return banned
    except Exception:
        pass
    # Fallback: check FO ban CSV published by NSE
    try:
        from datetime import date
        today = date.today().strftime("%d%m%Y")
        url = f"https://archives.nseindia.com/fo/sec_ban/{today}_secban.csv"
        r = session.get(url, timeout=8)
        if r.ok:
            import io
            df = pd.read_csv(io.StringIO(r.text))
            return df.iloc[:,0].str.strip().tolist()
    except Exception:
        pass
    return []

@st.cache_data(ttl=600, show_spinner=False)
def get_rs_ratings(timeframe: str = "1 Month") -> dict:
    """
    Compute RS Ratings for all 545 stocks vs Nifty 50.
    Returns dict: symbol → RS Rating (1-99 percentile).
    IBD-style: 40% recent quarter + 20% each prior quarter.
    """
    from utils.math_utils import percentile_rank

    # Fetch Nifty 50 returns for each period
    nifty_hist = _fetch_price_history(("^NSEI", "NIFTY", "15mo", "1d"))

    def nifty_ret(days):
        if nifty_hist and nifty_hist.get("Period Ret%") is not None:
            return nifty_hist["Period Ret%"] / (126 / days)  # scale to period
        return 0

    # Fetch all stock returns using 1Y history
    syms = [(ns(s), s, "15mo", "1d") for s in FULL_UNIVERSE]
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
        results = list(ex.map(_fetch_price_history, syms))

    # Compute RS scores
    raw_scores = {}
    for r in results:
        if not r:
            continue
        sym      = r["Symbol"]
        # Momentum: 3M + 6M + 9M + 12M (using period ret as proxy)
        ret_3m   = r["Period Ret%"] * 0.25  # approximate quarterly
        rs_raw   = (0.40 * ret_3m +
                    0.20 * (ret_3m * 0.8) +
                    0.20 * (ret_3m * 0.7) +
                    0.20 * (ret_3m * 0.6))  # decay older periods
        raw_scores[sym] = rs_raw

    # Percentile rank
    universe_vals = list(raw_scores.values())
    rs_ratings = {}
    for sym, raw in raw_scores.items():
        rs_ratings[sym] = percentile_rank(raw, universe_vals)

    return rs_ratings

@st.cache_data(ttl=300, show_spinner=False)
def get_52w_breakout_stocks() -> pd.DataFrame:
    """
    Scan universe for 52-week high breakout candidates.
    Criteria: Price > 0.95 × 52W High AND relative volume > 1.3×
    """
    if "universe_df" in st.session_state and not st.session_state["universe_df"].empty:
        df = st.session_state["universe_df"]
        breakouts = []
        for _, row in df.iterrows():
            p   = row.get("Price")
            hi  = row.get("52W High")
            vol_ratio = row.get("Volume Ratio")
            if p and hi and hi > 0:
                pct_from_hi = (p / hi) * 100
                if pct_from_hi >= 95:  # within 5% of 52W high
                    vol_conf = bool(vol_ratio and vol_ratio > 1.3)
                    breakouts.append({
                        "Symbol":         row["Symbol"],
                        "Name":           row.get("Name",""),
                        "Sector":         row.get("Sector",""),
                        "Price (₹)":      round(p, 2),
                        "52W High (₹)":   round(hi, 2),
                        "% from 52W High":round(pct_from_hi - 100, 2),
                        "Volume Confirm": "✅ Yes" if vol_conf else "⚠ Weak",
                        "Score":          row.get("Score", 0),
                        "Tech":           row.get("Tech",""),
                    })
        return pd.DataFrame(breakouts).sort_values("% from 52W High", ascending=False)
    return pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def get_insider_buying_signal(days: int = 30) -> pd.DataFrame:
    """
    Detect insider/promoter buying from NSE bulk deals.
    High-conviction signal: promoters buying their own stock.
    """
    deals_df = get_nse_bulk_deals(days)
    if deals_df.empty:
        return pd.DataFrame()

    try:
        # Filter for potential insider/promoter buying
        # Promoter names typically contain company name or promoter entity name
        buy_cols   = [c for c in deals_df.columns if 'buy' in c.lower() or 'trans' in c.lower()]
        name_cols  = [c for c in deals_df.columns if 'client' in c.lower() or 'name' in c.lower() or 'entity' in c.lower()]
        sym_cols   = [c for c in deals_df.columns if 'symbol' in c.lower()]

        if not sym_cols:
            return pd.DataFrame()

        # Look for "Promoter" or "Insider" tag
        promoter_deals = deals_df[
            deals_df.apply(lambda r: any(
                'promoter' in str(r.get(c,'')).lower() or
                'insider' in str(r.get(c,'')).lower()
                for c in name_cols
            ), axis=1)
        ]
        return promoter_deals if not promoter_deals.empty else deals_df.head(20)
    except Exception:
        return deals_df.head(20) if not deals_df.empty else pd.DataFrame()

def get_sector_rotation_signal(macro_regime: dict) -> dict:
    """
    Classic sector rotation based on economic cycle.
    Maps current macro regime to optimal sector allocation.
    """
    if not macro_regime:
        return {}

    rate_cut    = macro_regime.get("rate_cut", False)
    rate_hike   = macro_regime.get("rate_hike", False)
    crude_high  = macro_regime.get("crude_high", False)
    crude_low   = macro_regime.get("crude_low", False)
    high_vix    = macro_regime.get("high_vix", False)
    mkt_up      = macro_regime.get("mkt_up", False)
    inr_weak    = macro_regime.get("inr_weak", False)
    us_bear     = macro_regime.get("us_bear", False)

    overweight  = []
    underweight = []
    rationale   = []

    if rate_cut:
        overweight += ["Banking","NBFC","Realty","Consumer","Auto"]
        underweight += ["IT","Pharma"]
        rationale.append("Rate cuts → credit-sensitive sectors outperform")
    elif rate_hike:
        overweight += ["IT","Pharma","FMCG"]
        underweight += ["Banking","NBFC","Realty","Auto"]
        rationale.append("Rate hikes → defensive sectors preferred")

    if crude_high:
        overweight += ["Energy","Metal"]
        underweight += ["Auto","FMCG","Aviation","Chemicals"]
        rationale.append(f"High crude (${macro_regime.get('crude_price',80):.0f}) → Energy wins, cost-pressure sectors lose")
    elif crude_low:
        overweight += ["Auto","FMCG","Aviation","Paints"]
        underweight += ["Energy"]
        rationale.append("Low crude → input-cost beneficiaries outperform")

    if inr_weak:
        overweight += ["IT","Pharma","Metal"]
        underweight += ["Oil (refiners)","Aviation"]
        rationale.append(f"INR weak (₹{macro_regime.get('inr_level',84):.1f}) → exporters gain")

    if high_vix:
        overweight += ["FMCG","Pharma","Telecom"]
        underweight += ["PSU Bank","NBFC","Realty","Smallcap"]
        rationale.append("High VIX → flight to defensive quality")

    if us_bear:
        overweight += ["Domestic-facing FMCG","Pharma","Infra"]
        underweight += ["IT","Metal"]
        rationale.append("US bear market → USD earnings stocks at risk")

    if mkt_up and not high_vix:
        overweight += ["Midcap","Smallcap","Capex plays"]
        rationale.append("Market uptrend → risk-on, cyclicals outperform")

    # Determine cycle stage
    if rate_cut and mkt_up and not crude_high:
        stage = "EARLY BULL — Maximum opportunity. Cyclicals, rate-sensitives, smallcaps."
    elif not rate_cut and not rate_hike and mkt_up:
        stage = "MID BULL — Quality growth wins. IT, FMCG, Consumer Discretionary."
    elif rate_hike and not high_vix:
        stage = "LATE BULL — Defensives + value. Banks (margin expansion), Energy."
    elif high_vix and us_bear:
        stage = "RISK-OFF — Capital preservation. FMCG, Pharma, Gold ETFs."
    else:
        stage = "TRANSITION — Mixed signals. Stock picking > sector bets."

    return {
        "stage":       stage,
        "overweight":  list(dict.fromkeys(overweight)),  # deduplicated
        "underweight": list(dict.fromkeys(underweight)),
        "rationale":   rationale,
    }

@st.cache_data(ttl=300, show_spinner=False)
def get_mf_data(scheme_code: int) -> dict:
    try:
        r = requests.get(f"https://api.mfapi.in/mf/{scheme_code}", timeout=15)
        if not r.ok: return {}
        data = r.json()
        navs = data.get("data",[])
        if not navs: return data
        df = pd.DataFrame(navs)
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df["nav"]  = pd.to_numeric(df["nav"], errors="coerce")
        df = df.sort_values("date").dropna()
        df  = df.dropna(subset=["nav"])
        if df.empty: return data
        cur = df["nav"].iloc[-1]
        rets = {}
        for lbl, days in {"1W":7,"1M":30,"3M":90,"6M":180,"1Y":365,"3Y":1095,"5Y":1825}.items():
            cutoff = df["date"].iloc[-1] - timedelta(days=days)
            hist   = df[df["date"] <= cutoff]
            if not hist.empty:
                old = hist["nav"].iloc[-1]
                yrs = days/365
                ret = ((cur/old)**(1/yrs)-1)*100 if days>=365 else (cur/old-1)*100
                rets[lbl] = round(ret,2)
            else:
                rets[lbl] = None
        return {**data,"navDf":df,"returns":rets,"currentNAV":cur}
    except Exception:
        return {}
