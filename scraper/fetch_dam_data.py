import os
import re
import ssl
import sys
import subprocess
import urllib.request
import urllib.parse
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

MARATHI_DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# -----------------------------------------------------------------------------
# MASTER STATE DAM DICTIONARY (138 MAJOR & MEDIUM DAMS OF MAHARASHTRA)
# -----------------------------------------------------------------------------
MASTER_DAMS_DATA = [
    # PUNE REGION - Pune District
    {'en': 'Khadakwasla', 'mr': 'खडकवासला', 'district': 'Pune', 'division': 'Pune', 'keys': ['khadakwasla', 'खडकवासला']},
    {'en': 'Panshet', 'mr': 'पानशेत', 'district': 'Pune', 'division': 'Pune', 'keys': ['panshet', 'पानशेत', 'पानशत']},
    {'en': 'Varasgaon', 'mr': 'वरसगाव', 'district': 'Pune', 'division': 'Pune', 'keys': ['varasgaon', 'warasgaon', 'वरसगाव', 'वरसगांव']},
    {'en': 'Temghar', 'mr': 'टेमघर', 'district': 'Pune', 'division': 'Pune', 'keys': ['temghar', 'टेमघर', 'टमघर']},
    {'en': 'Mulshi', 'mr': 'मुळशी', 'district': 'Pune', 'division': 'Pune', 'keys': ['mulshi', 'mulshi tata', 'मुळशी', 'मुळशी टाटा', 'मळशी', 'मळशी टाटा']},
    {'en': 'Gunjawani', 'mr': 'गुंजवणी', 'district': 'Pune', 'division': 'Pune', 'keys': ['gunjawani', 'गुंजवणी', 'गजवणी']},
    {'en': 'Pavana', 'mr': 'पवना', 'district': 'Pune', 'division': 'Pune', 'keys': ['pawana', 'pavana', 'पवना', 'पावना']},
    {'en': 'Chaskaman', 'mr': 'चासकमान', 'district': 'Pune', 'division': 'Pune', 'keys': ['chaskaman', 'चासकमान']},
    {'en': 'Dimbhe', 'mr': 'डिंभे', 'district': 'Pune', 'division': 'Pune', 'keys': ['dimbhe', 'डिंभे', 'डंभे']},
    {'en': 'Bhama Askhed', 'mr': 'भामा आसखेड', 'district': 'Pune', 'division': 'Pune', 'keys': ['bhama askhed', 'भामा आसखेड', 'भामा आसखड']},
    {'en': 'Andra', 'mr': 'आंद्रा', 'district': 'Pune', 'division': 'Pune', 'keys': ['andra', 'आंद्रा']},
    {'en': 'Pimpalgaon Joge', 'mr': 'पिंपळगाव जोगे', 'district': 'Pune', 'division': 'Pune', 'keys': ['pimpalgaon joge', 'पिंपळगाव जोगे', 'पपळगाव जोगे']},
    {'en': 'Manikdoh', 'mr': 'माणिकडोह', 'district': 'Pune', 'division': 'Pune', 'keys': ['manikdoh', 'माणिकडोह', 'माणकडोह']},
    {'en': 'Yedgaon', 'mr': 'येडगाव', 'district': 'Pune', 'division': 'Pune', 'keys': ['yedgaon', 'येडगाव', 'यडगाव']},
    {'en': 'Wadaj', 'mr': 'वडज', 'district': 'Pune', 'division': 'Pune', 'keys': ['wadaj', 'वडज']},
    {'en': 'Ghod', 'mr': 'घोड (चिंचणी)', 'district': 'Pune', 'division': 'Pune', 'keys': ['ghod', 'ghod (chinchani)', 'घोड', 'घोड (चिंचणी)', 'घोड (चचणी)']},
    {'en': 'Visapur', 'mr': 'विसापूर', 'district': 'Pune', 'division': 'Pune', 'keys': ['visapur', 'विसापूर', 'वसापर']},
    {'en': 'Kalmodi', 'mr': 'कलमोडी', 'district': 'Pune', 'division': 'Pune', 'keys': ['kalmodi', 'कलमोडी']},
    {'en': 'Kasarsai', 'mr': 'कासारसाई', 'district': 'Pune', 'division': 'Pune', 'keys': ['kasarsai', 'कासारसाई']},
    {'en': 'Nira Deoghar', 'mr': 'नीरा देवघर', 'district': 'Pune', 'division': 'Pune', 'keys': ['nira deoghar', 'नीरा देवघर', 'नीरा दवघर']},
    {'en': 'Bhatghar', 'mr': 'भाटघर', 'district': 'Pune', 'division': 'Pune', 'keys': ['bhatghar', 'भाटघर']},
    {'en': 'Nazare', 'mr': 'नाझरे', 'district': 'Pune', 'division': 'Pune', 'keys': ['nazare', 'नाझरे']},
    {'en': 'Lonavala Tata', 'mr': 'लोणावळा टाटा', 'district': 'Pune', 'division': 'Pune', 'keys': ['lonavala tata', 'लोणावळा टाटा']},
    {'en': 'Walwhan Tata', 'mr': 'वळवण टाटा', 'district': 'Pune', 'division': 'Pune', 'keys': ['walwan tata', 'walwhan tata', 'वळवण टाटा']},
    {'en': 'Shirawta Tata', 'mr': 'शिरवटा टाटा', 'district': 'Pune', 'division': 'Pune', 'keys': ['shirawta tata', 'shirwata tata', 'शिरवटा टाटा', 'शरवटा टाटा']},
    {'en': 'Kundali Tata', 'mr': 'कडली टाटा', 'district': 'Pune', 'division': 'Pune', 'keys': ['kundali tata', 'कडली टाटा']},
    {'en': 'Thokerwadi Tata', 'mr': 'ठोकरवाडी टाटा', 'district': 'Pune', 'division': 'Pune', 'keys': ['thokerwadi tata', 'ठोकरवाडी टाटा']},

    # PUNE REGION - Satara, Solapur, Kolhapur, Sangli
    {'en': 'Ujani', 'mr': 'भीमा (उजनी)', 'district': 'Solapur', 'division': 'Pune', 'keys': ['ujani', 'bhima (ujjani)', 'भीमा (उजनी)', 'उजनी']},
    {'en': 'Koyna', 'mr': 'कोयना', 'district': 'Satara', 'division': 'Pune', 'keys': ['koyna', 'कोयना']},
    {'en': 'Dhom', 'mr': 'धोम', 'district': 'Satara', 'division': 'Pune', 'keys': ['dhom', 'धोम']},
    {'en': 'Dhom Balkawadi', 'mr': 'धोम बलकवडी', 'district': 'Satara', 'division': 'Pune', 'keys': ['dhom balkawadi', 'धोम बलकवडी']},
    {'en': 'Kanher', 'mr': 'कन्हेर', 'district': 'Satara', 'division': 'Pune', 'keys': ['kanher', 'कन्हेर', 'कहरे']},
    {'en': 'Urmodi', 'mr': 'उरमोडी', 'district': 'Satara', 'division': 'Pune', 'keys': ['urmodi', 'उरमोडी']},
    {'en': 'Tarali', 'mr': 'तारळी', 'district': 'Satara', 'division': 'Pune', 'keys': ['tarali', 'तारळी']},
    {'en': 'Veer', 'mr': 'वीर', 'district': 'Satara', 'division': 'Pune', 'keys': ['veer', 'वीर']},
    {'en': 'Radhanagari', 'mr': 'राधानगरी', 'district': 'Kolhapur', 'division': 'Pune', 'keys': ['radhanagari', 'radhanagari h e p', 'राधानगरी', 'राधानगरी ज. िव. कप']},
    {'en': 'Dudhganga', 'mr': 'दूधगंगा', 'district': 'Kolhapur', 'division': 'Pune', 'keys': ['dudhganga', 'दूधगंगा', 'दध']},
    {'en': 'Tulshi', 'mr': 'तुळशी', 'district': 'Kolhapur', 'division': 'Pune', 'keys': ['tulshi', 'तुळशी', 'तळशी']},
    {'en': 'Warna', 'mr': 'वारणा', 'district': 'Kolhapur', 'division': 'Pune', 'keys': ['warna', 'वारणा']},

    # KOKAN REGION - Thane, Palghar, Raigad, Sindhudurg
    {'en': 'Bhatsa', 'mr': 'भातसा', 'district': 'Thane', 'division': 'Kokan', 'keys': ['bhatsa', 'भातसा', 'भातासा']},
    {'en': 'Tansa', 'mr': 'तानसा', 'district': 'Thane', 'division': 'Kokan', 'keys': ['tansa', 'तानसा']},
    {'en': 'Modak Sagar', 'mr': 'मोडक सागर', 'district': 'Thane', 'division': 'Kokan', 'keys': ['modaksagar', 'modak sagar', 'मोडक सागर', 'मोडकसागर']},
    {'en': 'Middle Vaitarna', 'mr': 'मध्य वैतरणा', 'district': 'Thane', 'division': 'Kokan', 'keys': ['middle vaitarna', 'मध्य वैतरणा', 'मय वतरणा']},
    {'en': 'Barvi', 'mr': 'बारवी', 'district': 'Thane', 'division': 'Kokan', 'keys': ['barvi', 'बारवी']},
    {'en': 'Lower Chondhe', 'mr': 'निम्न चोंढे', 'district': 'Thane', 'division': 'Kokan', 'keys': ['lower chondhe', 'निम्न चोंढे']},
    {'en': 'Upper Ghatghar', 'mr': 'ऊर्ध्व घाटघर', 'district': 'Thane', 'division': 'Kokan', 'keys': ['upper ghatghar', 'ऊर्ध्व घाटघर', 'ऊव घाटघर']},
    {'en': 'Dhamni', 'mr': 'धामणी', 'district': 'Palghar', 'division': 'Kokan', 'keys': ['dhamni', 'धामणी', 'सूर्या']},
    {'en': 'Kawdas P. U. Weir', 'mr': 'कवडास पिकअप बंधारा', 'district': 'Palghar', 'division': 'Kokan', 'keys': ['kawdas p. u. weir', 'कवडास व. ब.ं']},
    {'en': 'Dolwahal weir', 'mr': 'डोलवाहाल पिकअप बंधारा', 'district': 'Raigad', 'division': 'Kokan', 'keys': ['dolwahal weir', 'डोलवाहल ब.ं']},
    {'en': 'Tillari', 'mr': 'तिल्लारी', 'district': 'Sindhudurg', 'division': 'Kokan', 'keys': ['tillari', 'tillari (dhamne)', 'तिल्लारी', 'तारी', 'तारी (धामण)े']},

    # NASHIK REGION - Nashik, Ahilyanagar, Jalgaon
    {'en': 'Bhandardara', 'mr': 'भांडारदरा', 'district': 'Ahmednagar', 'division': 'Nashik', 'keys': ['bhandardara', 'भांडारदरा', 'भडारदरा']},
    {'en': 'Mula', 'mr': 'मुळा', 'district': 'Ahmednagar', 'division': 'Nashik', 'keys': ['mula', 'मुळा', 'मळा']},
    {'en': 'Nilwande-2', 'mr': 'निळवंडे', 'district': 'Ahmednagar', 'division': 'Nashik', 'keys': ['nilwande', 'nilwande-2', 'निळवंडे', 'ननळवड-2']},
    {'en': 'Upper Tapi Hatnur', 'mr': 'ऊर्ध्व तापी हतनूर', 'district': 'Jalgaon', 'division': 'Nashik', 'keys': ['upper tapi hatnur', 'hatnur', 'हतनूर', 'ऊर्ध्व तापी हतनूर', 'ऊव तापी हतनरू']},
    {'en': 'Waghur', 'mr': 'वाघूर', 'district': 'Jalgaon', 'division': 'Nashik', 'keys': ['waghur', 'वाघूर', 'वाघरू']},
    {'en': 'Arjunsagar', 'mr': 'अर्जुनसागर', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['arjunsagar', 'अर्जुनसागर']},
    {'en': 'Bham Dam', 'mr': 'भाम धरण', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['bham dam', 'भाम धरण']},
    {'en': 'Bhavali', 'mr': 'भावली', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['bhavali', 'भावली']},
    {'en': 'Chankapur', 'mr': 'चणकापूर', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['chankapur', 'चणकापूर', 'चणकापरू']},
    {'en': 'Darna', 'mr': 'दारणा', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['darna', 'दारणा']},
    {'en': 'Gangapur', 'mr': 'गंगापूर', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['gangapur', 'गंगापूर', 'गगा']},
    {'en': 'Girna', 'mr': 'गिरणा', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['girna', 'गिरणा', 'गरणा']},
    {'en': 'Kadwa', 'mr': 'कडवा', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['kadwa', 'कडवा']},
    {'en': 'Karanjwan', 'mr': 'करंजवण', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['karanjwan', 'करंजवण', 'करजवण']},
    {'en': 'Mukane', 'mr': 'मुकणे', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['mukane', 'मुकणे', 'मदनसरी']},
    {'en': 'Ozarkhed', 'mr': 'ओझरखेड', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['ozarkhed', 'ozarkhed dam', 'ओझरखेड', 'ओझरखड']},
    {'en': 'Palkhed', 'mr': 'पालखेड', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['palkhed', 'पालखेड', 'पालखड']},
    {'en': 'Punegaon', 'mr': 'पुणेगाव', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['punegaon', 'पुणेगाव']},
    {'en': 'Tisgaon', 'mr': 'तिसगाव', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['tisgaon', 'तिसगाव', 'तसगाव']},
    {'en': 'Upper Vaitarna', 'mr': 'वैतरणा', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['upper vaitarna', 'vaitarna', 'वैतरणा', 'वतरणा', 'वतरणा ज. िव. कप']},
    {'en': 'Waghad', 'mr': 'वाघाड', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['waghad', 'वाघाड']},
    {'en': 'Waki Dam', 'mr': 'वाकी धरण', 'district': 'Nashik', 'division': 'Nashik', 'keys': ['waki dam', 'वाकी धरण', 'वाक धरण']},

    # CHHATRAPATI SAMBHAJINAGAR REGION
    {'en': 'Jayakwadi (Paithan)', 'mr': 'जयकवाडी (पैठण)', 'district': 'Chhatrapati Sambhajinagar', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['paithan (jayakwadi)', 'jayakwadi', 'paithan', 'जयकवाडी', 'पैठण', 'पठण', 'जयकवाडी (पैठण)']},
    {'en': 'Apegaon H L B', 'mr': 'आपगाव उच्च पातळी बंधारा', 'district': 'Chhatrapati Sambhajinagar', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['apegaon h l b', 'आपगाव उ त.ब.ं']},
    {'en': 'Majalgaon', 'mr': 'माजलगाव', 'district': 'Beed', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['majalgaon', 'माजलगाव']},
    {'en': 'Manjara', 'mr': 'मांजरा', 'district': 'Beed', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['manjara', 'मांजरा', 'माजरा']},
    {'en': 'Dhanegaon High Level Barrage', 'mr': 'धनेगाव उच्च पातळी बंधारा', 'district': 'Beed', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['dhanegaon high level barrage', 'धनगाव उ. त. ब.ं']},
    {'en': 'Dongargaon H L B', 'mr': 'डोंगरगाव उच्च पातळी बंधारा', 'district': 'Beed', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['dongargaon h l b', 'डगरगाव उ. त. ब.ं']},
    {'en': 'Siddheshwar', 'mr': 'सिद्धेश्वर', 'district': 'Hingoli', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['siddheshwar', 'सिद्धेश्वर', 'सदर']},
    {'en': 'Yeldari', 'mr': 'येळदारी', 'district': 'Hingoli', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['yeldari', 'येळदारी', 'यलदरी']},
    {'en': 'Amdura', 'mr': 'आमदुरा', 'district': 'Nanded', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['amdura', 'अमदरा']},
    {'en': 'Dhalegaon H L B', 'mr': 'ढालेगाव उच्च पातळी बंधारा', 'district': 'Nanded', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['dhalegaon h l b', 'ढालगाव उ. त. ब.ं']},
    {'en': 'Lower Manar', 'mr': 'निम्न मानार', 'district': 'Nanded', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['lower manar', 'निम्न मानार', 'नन मनार']},
    {'en': 'Vishnupuri', 'mr': 'विष्णुपूरी', 'district': 'Nanded', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['vishnupuri', 'विष्णुपूरी']},
    {'en': 'Lower Terna', 'mr': 'निम्न तेरणा', 'district': 'Dharashiv', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['lower terna', 'निम्न तेरणा', 'नन तरणा']},
    {'en': 'Sina kolegaon', 'mr': 'सीना कोळेगाव', 'district': 'Dharashiv', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['sina kolegaon', 'सना कोळगाव']},
    {'en': 'Lower Dudhana', 'mr': 'निम्न दुधना', 'district': 'Parbhani', 'division': 'Chhatrapati Sambhajinagar', 'keys': ['lower dudhana', 'निम्न दुधना', 'नन दधना']},

    # AMRAVATI REGION
    {'en': 'Upper Wardha', 'mr': 'ऊर्ध्व वर्धा', 'district': 'Amravati', 'division': 'Amravati', 'keys': ['upper wardha', 'ऊर्ध्व वर्धा', 'ऊव वधा']},
    {'en': 'Arunavati', 'mr': 'अरुणावती', 'district': 'Yavatmal', 'division': 'Amravati', 'keys': ['arunavati', 'अरुणावती', 'अणावती']},
    {'en': 'Bembla', 'mr': 'बेम्बळा', 'district': 'Yavatmal', 'division': 'Amravati', 'keys': ['bembla', 'बेम्बळा', 'बबळा']},
    {'en': 'Isapur', 'mr': 'इसापूर', 'district': 'Yavatmal', 'division': 'Amravati', 'keys': ['isapur', 'इसापूर', 'इसापरू']},
    {'en': 'Pus', 'mr': 'पूस', 'district': 'Yavatmal', 'division': 'Amravati', 'keys': ['pus', 'पूस', 'पस']},
    {'en': 'Wan', 'mr': 'वान', 'district': 'Akola', 'division': 'Amravati', 'keys': ['wan', 'वान']},
    {'en': 'Katepurna', 'mr': 'काटेपूर्णा', 'district': 'Akola', 'division': 'Amravati', 'keys': ['katepurna', 'काटेपूर्णा', 'काटेपण']},
    {'en': 'Khadakpurna', 'mr': 'खडकपूर्णा', 'district': 'Buldhana', 'division': 'Amravati', 'keys': ['khadakpurna', 'खडकपूर्णा', 'खडकपण']},
    {'en': 'Nalganga', 'mr': 'नळगंगा', 'district': 'Buldhana', 'division': 'Amravati', 'keys': ['nalganga', 'नळगंगा', 'नळगगा']},
    {'en': 'Pentakli', 'mr': 'पेनटाकळी', 'district': 'Buldhana', 'division': 'Amravati', 'keys': ['pentakli', 'पेनटाकळी', 'पनटाकळी']},

    # NAGPUR REGION
    {'en': 'Bawanthadi', 'mr': 'बावनथडी', 'district': 'Bhandara', 'division': 'Nagpur', 'keys': ['bawanthadi', 'बावनथडी']},
    {'en': 'Gosikhurd', 'mr': 'गोसीखुर्द', 'district': 'Bhandara', 'division': 'Nagpur', 'keys': ['gosikhurd', 'गोसीखुर्द', 'गोसीखद']},
    {'en': 'Asolamendha', 'mr': 'असोलामेंढा', 'district': 'Chandrapur', 'division': 'Nagpur', 'keys': ['asolamendha', 'असोलामेंढा', 'असोलामढा']},
    {'en': 'Dina', 'mr': 'दिना', 'district': 'Gadchiroli', 'division': 'Nagpur', 'keys': ['dina', 'दिना', 'दना']},
    {'en': 'Dhapewada', 'mr': 'धापवाडा', 'district': 'Gondia', 'division': 'Nagpur', 'keys': ['dhapewada', 'धापवाडा']},
    {'en': 'Itiadoh', 'mr': 'इटीयाडोह', 'district': 'Gondia', 'division': 'Nagpur', 'keys': ['itiadoh', 'इटीयाडोह', 'इटयाडोह']},
    {'en': 'Kalisarar', 'mr': 'कालीसरार', 'district': 'Gondia', 'division': 'Nagpur', 'keys': ['kalisarar', 'कालीसरार']},
    {'en': 'Pujaritola P.U.Weir', 'mr': 'पुजारीटोला', 'district': 'Gondia', 'division': 'Nagpur', 'keys': ['pujaritola', 'pujaritola p.u.weir', 'पुजारीटोला']},
    {'en': 'Sirpur', 'mr': 'सिरपूर', 'district': 'Gondia', 'division': 'Nagpur', 'keys': ['sirpur', 'सिरपूर', 'सरपरू']},
    {'en': 'Kamthi Khairy', 'mr': 'कामठी खैरी', 'district': 'Nagpur', 'division': 'Nagpur', 'keys': ['kamthi khairy', 'kamthi khairi', 'कामठी खैरी', 'कामठी खरी']},
    {'en': 'Khindsi', 'mr': 'खिडसी', 'district': 'Nagpur', 'division': 'Nagpur', 'keys': ['khindsi', 'खिडसी', 'खडसी']},
    {'en': 'Nand', 'mr': 'नांद', 'district': 'Nagpur', 'division': 'Nagpur', 'keys': ['nand', 'नांद', 'नाद']},
    {'en': 'Totladoh', 'mr': 'तोतलाडोह', 'district': 'Nagpur', 'division': 'Nagpur', 'keys': ['totladoh', 'तोतलाडोह']},
    {'en': 'Wadgaon', 'mr': 'वडगाव', 'district': 'Nagpur', 'division': 'Nagpur', 'keys': ['wadgaon', 'वडगाव']},
    {'en': 'Bor', 'mr': 'बोर', 'district': 'Wardha', 'division': 'Nagpur', 'keys': ['bor', 'बोर']},
    {'en': 'Lower Wardha', 'mr': 'निम्न वर्धा', 'district': 'Wardha', 'division': 'Nagpur', 'keys': ['lower wardha', 'निम्न वर्धा', 'नन वधा']}
]

# Build quick lookup mapping table
DAM_LOOKUP = {}
for entry in MASTER_DAMS_DATA:
    info = {
        'en': entry['en'],
        'mr': entry['mr'],
        'district': entry['district'],
        'division': entry['division']
    }
    DAM_LOOKUP[entry['en'].lower()] = info
    DAM_LOOKUP[entry['mr'].lower()] = info
    for k in entry['keys']:
        DAM_LOOKUP[k.lower()] = info

def clean_marathi_text(text):
    """Strips PDF font ligature artifact symbols from Marathi text."""
    if not text: return ""
    cleaned = re.sub(r'[\uE000-\uF8FF]', '', text).strip()
    return cleaned if cleaned else text

def get_pdf_text(pdf_path):
    """Extract text from PDF using pdftotext CLI, pypdf, or pdfplumber."""
    try:
        res = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout
    except Exception:
        pass

    if HAS_PYPDF:
        try:
            reader = pypdf.PdfReader(pdf_path)
            text = "".join(page.extract_text() or "" for page in reader.pages)
            if text.strip():
                return text
        except Exception:
            pass

    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "".join((page.extract_text() or "") + "\n" for page in pdf.pages)
                if text.strip():
                    return text
        except Exception:
            pass

    return ""

def parse_dam_line(line, active_division="Pune", active_district="Pune"):
    """Parses a single line containing dam storage data from English or Marathi PDF."""
    line_trans = line.translate(MARATHI_DIGITS)
    tokens = line_trans.split()
    
    date_idx = -1
    for i, t in enumerate(tokens):
        if re.match(r'^\d{2}/\d{2}/\d{4}$', t):
            date_idx = i
            break

    if date_idx >= 1 and len(tokens) >= date_idx + 7:
        name_tokens = [t for t in tokens[:date_idx] if not re.match(r'^\d+$', t)]
        raw_dam_name = clean_marathi_text(' '.join(name_tokens)).strip()
        if not raw_dam_name:
            raw_dam_name = clean_marathi_text(tokens[date_idx - 1])
            
        dict_info = DAM_LOOKUP.get(raw_dam_name.lower())
        if not dict_info and len(name_tokens) > 0:
            dict_info = DAM_LOOKUP.get(name_tokens[-1].lower())
            
        if dict_info:
            dam_name_en = dict_info['en']
            dam_name_mr = dict_info['mr']
            district = dict_info['district']
            division = dict_info['division']
        else:
            dam_name_en = raw_dam_name
            dam_name_mr = raw_dam_name
            district = active_district
            division = active_division

        report_date = tokens[date_idx]
        report_time = tokens[date_idx+1]
        if date_idx + 2 < len(tokens) and tokens[date_idx+2] in ['स.', 'वा.', 'AM', 'PM', 'am', 'pm']:
            report_time += ' ' + tokens[date_idx+2]
            idx_offset = date_idx + 3
        else:
            idx_offset = date_idx + 2
            
        if len(tokens) >= idx_offset + 6:
            dead = tokens[idx_offset]
            design_live = tokens[idx_offset+1]
            design_gross = tokens[idx_offset+2]
            current_live = tokens[idx_offset+3]
            current_gross = tokens[idx_offset+4]
            current_pct_raw = tokens[idx_offset+5].replace('%', '')
            
            last_year_pct = "0"
            if len(tokens) > idx_offset + 6:
                for tok in tokens[idx_offset+6:]:
                    cleaned = tok.replace('%', '')
                    if re.match(r'^\d+(\.\d+)?$', cleaned):
                        last_year_pct = cleaned
                        break

            dead_val = float(dead) if re.match(r'^\d+(\.\d+)?$', dead) else 0.0
            design_live_val = float(design_live) if re.match(r'^\d+(\.\d+)?$', design_live) else 0.0
            design_gross_val = float(design_gross) if re.match(r'^\d+(\.\d+)?$', design_gross) else 0.0
            current_live_val = float(current_live) if re.match(r'^\d+(\.\d+)?$', current_live) else 0.0
            current_gross_val = float(current_gross) if re.match(r'^\d+(\.\d+)?$', current_gross) else 0.0
            
            if re.match(r'^\d+(\.\d+)?$', current_pct_raw) and float(current_pct_raw) > 0:
                current_pct_val = float(current_pct_raw)
            elif design_live_val > 0 and current_live_val >= 0:
                current_pct_val = round((current_live_val / design_live_val) * 100, 2)
            else:
                current_pct_val = 0.0

            return {
                'Dam Name': dam_name_en,
                'Dam Name MR': dam_name_mr,
                'District': district,
                'Division': division,
                'Report Date': report_date,
                'Report Time': report_time,
                'Dead Storage (MCM)': dead_val,
                'Design Live Storage (MCM)': design_live_val,
                'Design Gross Storage (MCM)': design_gross_val,
                'Current Live Storage (MCM)': current_live_val,
                'Current Gross Storage (MCM)': current_gross_val,
                'Current Live Storage (%)': min(150.0, max(0.0, current_pct_val)),
                'Last Year Storage (%)': float(last_year_pct) if re.match(r'^\d+(\.\d+)?$', last_year_pct) else 0.0,
                'Status': 'Success'
            }
    return None

def extract_all_dams_from_pdf(pdf_path, dt_str):
    """Extracts storage metrics for all dams in Maharashtra from a single PDF using section tracking."""
    results = []
    if not pdf_path or not os.path.exists(pdf_path):
        return results

    text = get_pdf_text(pdf_path)
    lines = text.split('\n')
    
    current_div = 'Pune'
    current_dist = 'Pune'
    
    for line in lines:
        stripped = line.strip()
        cleaned_line = clean_marathi_text(stripped)
        
        # Section Header Tracking
        if 'Nagpur Region' in stripped or 'नागपूर' in cleaned_line:
            current_div = 'Nagpur'
        elif 'Amravti Region' in stripped or 'Amravati Region' in stripped or 'अमरावती' in cleaned_line:
            current_div = 'Amravati'
        elif 'Chhatrapati Sambhajinagar Region' in stripped or 'संभाजीनगर' in cleaned_line or 'सभाजीनगर' in cleaned_line:
            current_div = 'Chhatrapati Sambhajinagar'
        elif 'Nashik Region' in stripped or 'नाशिक' in cleaned_line or 'नाशक' in cleaned_line:
            current_div = 'Nashik'
        elif 'Pune Region' in stripped or 'पुणे' in cleaned_line or 'प ण' in cleaned_line:
            current_div = 'Pune'
        elif 'Kokan Region' in stripped or 'कोकण' in cleaned_line:
            current_div = 'Kokan'

        parsed = parse_dam_line(line, active_division=current_div, active_district=current_dist)
        if parsed:
            results.append(parsed)
            
    return results

def organize_existing_pdfs(pdf_dir='dam_pdfs'):
    """Organizes flat PDF files into pdf_dir/YYYY/MM/ subfolders."""
    if not os.path.exists(pdf_dir):
        return
    moved_count = 0
    for item in os.listdir(pdf_dir):
        item_path = os.path.join(pdf_dir, item)
        if os.path.isfile(item_path) and item.startswith("report_") and item.endswith(".pdf"):
            match = re.search(r'report_(\d{2})-(\d{2})-(\d{4})\.pdf', item)
            if match:
                day, month, year = match.groups()
                target_dir = os.path.join(pdf_dir, year, month)
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, item)
                if not os.path.exists(target_path):
                    os.rename(item_path, target_path)
                else:
                    os.remove(item_path)
                moved_count += 1
    if moved_count > 0:
        print(f"📁 Organized {moved_count} existing flat PDFs into YYYY/MM subfolders.")

def download_pdf_for_date(date_obj, pdf_dir):
    """Downloads daily PDF for given date into pdf_dir/YYYY/MM/report_DD-MM-YYYY.pdf."""
    dt_str = date_obj.strftime('%d-%m-%Y')
    year_str = date_obj.strftime('%Y')
    month_str = date_obj.strftime('%m')
    
    if date_obj.year < 2024:
        return dt_str, None, False

    sub_dir = os.path.join(pdf_dir, year_str, month_str)
    os.makedirs(sub_dir, exist_ok=True)
    
    dest_path = os.path.join(sub_dir, f"report_{dt_str}.pdf")
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        return dt_str, dest_path, True

    base_url = 'https://wrd.maharashtra.gov.in/Upload/PDF/'
    patterns = [
        "Today's-Storage-ReportEng-{date}.pdf",
        "Today's Storage ReportEng-{date}.pdf",
        "Today-Storage-ReportEng-{date}.pdf",
        "Today's-Storage-ReportMarathi-{date}.pdf",
        "Today's Storage ReportMarathi-{date}.pdf",
        "Today's-Storage-Report-{date}.pdf"
    ]

    for pat in patterns:
        filename = pat.format(date=dt_str)
        url = base_url + urllib.parse.quote(filename)
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=10) as resp:
                data = resp.read()
                if len(data) > 1000:
                    with open(dest_path, 'wb') as f:
                        f.write(data)
                    return dt_str, dest_path, True
        except Exception:
            continue

    return dt_str, None, False

def fetch_multi_dam_data(days=1000, pdf_dir='dam_pdfs', max_download_workers=15, max_extract_workers=16):
    """Downloads PDFs for date range and extracts data for ALL state dams."""
    os.makedirs(pdf_dir, exist_ok=True)
    organize_existing_pdfs(pdf_dir)
    today = datetime.now()
    dates = [today - timedelta(days=i) for i in range(days)]
    
    print(f"[*] Starting download & state-wide extraction across {days} requested dates...")
    
    pdf_files = {}
    
    # 1. Gather all existing local PDFs from dam_pdfs directory tree
    for root, _, files in os.walk(pdf_dir):
        for f in files:
            if f.startswith("report_") and f.endswith(".pdf"):
                m = re.search(r'report_(\d{2}-\d{2}-\d{4})\.pdf', f)
                if m:
                    dt_key = m.group(1)
                    pdf_files[dt_key] = os.path.join(root, f)
                    
    print(f"[*] Found {len(pdf_files)} pre-existing PDF reports in '{pdf_dir}'.")
    
    # 2. Download any missing dates in parallel
    missing_dates = [d for d in dates if d.strftime('%d-%m-%Y') not in pdf_files]
    if missing_dates:
        print(f"[*] Downloading {len(missing_dates)} missing PDF reports from WRD portal...")
        with ThreadPoolExecutor(max_workers=max_download_workers) as executor:
            futures = {executor.submit(download_pdf_for_date, d, pdf_dir): d for d in missing_dates}
            for future in as_completed(futures):
                dt_str, pdf_path, success = future.result()
                if success:
                    pdf_files[dt_str] = pdf_path

    print(f"[*] Total active PDF reports ready for processing: {len(pdf_files)}.")
    
    valid_items = sorted(pdf_files.items(), key=lambda x: datetime.strptime(x[0], '%d-%m-%Y'), reverse=True)
    print(f"[*] Parsing all Maharashtra state dams from {len(valid_items)} PDF reports in parallel...")

    all_records = []
    completed = 0
    with ThreadPoolExecutor(max_workers=max_extract_workers) as executor:
        futures = {executor.submit(extract_all_dams_from_pdf, path, dt_str.replace('-', '/')): dt_str for dt_str, path in valid_items}
        for future in as_completed(futures):
            dam_results = future.result()
            for rec in dam_results:
                all_records.append(rec)
            completed += 1
            if completed % 100 == 0 or completed == len(valid_items):
                print(f"    -> Progress: [{completed}/{len(valid_items)}] PDF reports processed.")

    df = pd.DataFrame(all_records)
    
    if not df.empty and 'Report Date' in df.columns:
        df['SortDate'] = df['Report Date'].apply(lambda x: datetime.strptime(str(x), '%d/%m/%Y') if re.match(r'\d{2}/\d{2}/\d{4}', str(x)) else datetime.min)
        df = df.sort_values(by=['SortDate', 'Dam Name'], ascending=[False, True]).drop(columns=['SortDate'])
    
    return df

def save_to_files(df):
    """
    Ingests scraped state records into SQLite relational DBMS ('pune_dams.db') via UPSERT,
    and exports the complete database back to JSON for the web dashboard.
    """
    db_dir = os.path.join(os.path.dirname(__file__), '..', 'database')
    if db_dir not in sys.path:
        sys.path.append(db_dir)
    import db_manager

    db_manager.init_db()

    if not df.empty and 'Dam Name' in df.columns:
        db_manager.ingest_records_from_dataframe(df)

    db_manager.export_db_to_json()

if __name__ == '__main__':
    days = 1000
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            pass

    df = fetch_multi_dam_data(days=days)
    save_to_files(df)
