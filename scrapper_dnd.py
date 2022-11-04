from bs4 import BeautifulSoup
import requests


def request_monster(url):
    requete = requests.get(url)
    page = requete.content
    soup = BeautifulSoup(page)
    #Nom
    h1 = soup.find("h1")
    nom = h1.string.strip()
    if str(nom) == "Ptéranodon" or str(nom) == "Satyre":
        return nom, ("13", "13", "1/4"), (12, 15, 10, 2, 9, 5), ["Morsure", 3, 6]
    #CA & PV
    soup_ca_pv = soup.find_all("div", {"class" : "red"} )
    def extract_CA_and_PV(soup_ca_pv):
        string = str(soup_ca_pv)
        ca = ""
        pv = ""
        puissance = ""
        i = 15
        while string[i-18:i] != "d'armure</strong> " and string[i-3:i] != "</p":
            i+=1
        while string[i] in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] and string[i-3:i] != "</p":
            ca+=string[i]
            i+=1
        while string[i-23:i] != "Points de vie</strong> " and string[i-3:i] != "</p":
            i+=1
        while string[i] != " " and string[i-3:i] != "</p":
            pv+=string[i]
            i+=1
        while string[i-19:i] !="Puissance</strong> " and string[i-9:i] != "PX)</div>":
            i+=1
        while string[i] != " " and string[i-9:i] != "PX)</div>":
            puissance+=string[i]
            i+=1
        return ca, pv, puissance
        return ca, pv
    l_ca_pv_pui = extract_CA_and_PV(soup_ca_pv)
    #CARACTERISTIQUES
    carac = soup.find_all("div", {"class" : "carac"} )
    def extract_carac(soup_carac):
        string = str(soup_carac)
        carac = ""
        i = 5
        while string[i-3:i] != "r/>" and string[i-3:i] != "</p":
            i+=1
        while string[i] != " " and string[i-3:i] != "</p":
            carac+=string[i]
            i+=1
        return carac
    l_carac = [extract_carac(soup_carac) for soup_carac in carac]
    # ACTIONS
    l_soup_action = soup.find_all("p")
    def extract_action(soup_action):
        string = str(soup_action)
        nom = ""
        bonus_touche = ""
        degat = ""
        l_chiffres = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        i = 15
        while string[i] != "<":
            nom+=string[i]
            i+=1
        while string[i] != "+" and string[i-3:i] != "</p":
            i+=1
        while string[i] != " " and string[i-3:i] != "</p":
            bonus_touche+=string[i]
            i+=1
        while string[i-2:i] != ": " and string[i-3:i] != "</p":
            i+=1
        while string[i] != " "  and string[i-3:i] != "</p":
            if string[i] in l_chiffres:
                degat+=string[i]
            i+=1
        #bonus_touche = int(bonus_touche)
        #degat = int(degat)
        return nom, bonus_touche, degat
    l_action = [extract_action(soup_action) for soup_action in l_soup_action]
    def detect_mot(string, liste_mot):
        string = str(string).lower()
        l_detect = []
        for mot in liste_mot:
            if mot.lower() in string:
                l_detect.append(mot)
        return l_detect
    
    def chiffre_to_int(chiffre):
        l_chiffres = ["une", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
        return l_chiffres.index(chiffre)+1

    def traitement_attaque_multiple(string_soup_multiple, l_nom_attaque):
        string = str(string_soup_multiple)
        attaque_in_multiple = detect_mot(string, l_nom_attaque)
        l_chiffres = ["une", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
        chiffre = detect_mot(string, l_chiffres)
        if len(attaque_in_multiple) == 0 or len(chiffre) == 0:#cas de l'hydre pour où len(chiffre) == 0 car c'est littéral
            return []
        if len(attaque_in_multiple) == 1:
            nb_attaque_1 = chiffre_to_int(chiffre[0])
            return ["Multiple", attaque_in_multiple[0], nb_attaque_1, "Rien", 0]
        elif len(attaque_in_multiple) == 2: #deux attaques
            l_int = []
            for c in chiffre:
                l_int.append(chiffre_to_int(c))
            if max(l_int) == 2:#max deux : donc une attaque de chaque
                return ["Multiple", attaque_in_multiple[0], 1, attaque_in_multiple[1], 1]
            else:
                return ["Multiple", "Rien", 100, "Rien", 0]
        else: #Plus de deux attaques
            return ["Multiple", "Rien", 0, "Rien", 100]

    def post_traitement(l_action, l_soup_action):
        # supprime les actions hors combat
        # met les actions simples sous forme de liste [nom, bonus_touche, degat]
        # ajoute en dernier la liste des attaques multiples ['Multiple', nom1, nb1, nom2, nb2]
        liste_action = []
        liste_multiple = []
        l_nom = []
        for tuple_action in l_action:
            if "multiple".lower() not in tuple_action[0]:
                if tuple_action[1] != '' and tuple_action[2] != '':#le 1 peut être +x puis on indique une liste de sorts !
                    liste_action.append([tuple_action[0], int(tuple_action[1]), int(tuple_action[2])])
                    l_nom.append(tuple_action[0])
        for action_soup in l_soup_action:
            if "multiple".lower() in str(action_soup):
                liste_multiple = traitement_attaque_multiple(action_soup, l_nom)
                if liste_multiple != []:
                    liste_action.append(liste_multiple)

            
        return liste_action
    
    l_action = post_traitement(l_action, l_soup_action)

    return nom, l_ca_pv_pui, l_carac, l_action

def request_all_monster(original_link = "https://www.aidedd.org/dnd-filters/monstres.php"):
    requete = requests.get(original_link)
    page = requete.content
    soup = BeautifulSoup(page)
    soup_link = soup.find_all("td", {"class" : "item"} )
    def extract_link(soup_link):
        string = str(soup_link)
        link = ""
        i = 10
        while string[i-9:i] != "<a href=\"" and string[i-5:i] != "</td>":
            i+=1
        while string[i] != "\"" and string[i-5:i] != "</td>":
            link+=string[i]
            i+=1
        return link
    list_link = []
    data = []
    def extracted_to_pre_csv(nom, l_ca_pv_pui, l_carac, l_action):
        data = []
        data.append(nom)
        ca, pv, pui = l_ca_pv_pui
        data.append(int(ca))
        data.append(int(pv))
        if len(pui) >= 3:
            num,den = pui.split( '/' )
            num, den
            data.append(float(num)/float(den))
        else:
            data.append(int(pui))
        for carac in l_carac:
            data.append(int(carac))
        data.append(l_action)
        for action in l_action:
            data.append(action)
        for i in range(len(l_action), 4):
            data.append(None)

        return data
    for link in soup_link[:50]:
        #list_link.append(extract_link(link))
        nom, l_ca_pv_pui, l_carac, l_action = request_monster(extract_link(link))
        print(nom)
        data.append(extracted_to_pre_csv(nom, l_ca_pv_pui, l_carac, l_action))
    return data
