
import json
import urllib.request
import pandas as pd
import sqlite3
import sys


# représente le profil choisi par l'utilisateur
class Taste:
    def __init__(self):
        self.name_taste = "default_name"
        self.food_list = []

    def set_name_taste(self, name_taste):
        self.name_taste = name_taste
        meats_profil = ["Meats", "meats"]
        veggie_profil = ["Veggie", "vegetable", "cereals and potatoes"]
        cocoa_profil = ["Cocoa", "cocoa", "Sugary snacks"]
        fruit_profil = ["Fruits", "fruits", "dairies"]
        list_profil = [meats_profil, veggie_profil, cocoa_profil, fruit_profil]
        for profil in list_profil:
            if profil[0] == name_taste:
                self.food_list = profil[1:]



class Persona:
    def __init__(self):
        self.taste = Taste()
        # Liste contenant les ingrédients exclus de la recherche
        self.list_avoid = []
        # Dict contenant le produit de départ
        self.research1 = dict()
        # Dict contenant le produit d'arrivée
        self.research2 = dict()

    # Permet de créer la table et de s'assurer qu'elle existe
    def ensure_table_exists(self):
        # Connexion à la BDD
        conn = sqlite3.connect("foody.db")
        cursor = conn.cursor()

        # Création d'une table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Historic
        (
            id INT PRIMARY KEY,
            taste VARCHAR(50),
            category VARCHAR(50),
            product_name VARCHAR(200),
            stores VARCHAR(200),
            purchase_places VARCHAR(200),
            url VARCHAR(400)
        );
        """)
        conn.close()

    # Affiche le menu de départ
    def first(self):
        self.ensure_table_exists()
        r_correct = False
        while r_correct != True:
            print(" Bonjour, Que souhaitez-vous faire ?")
            print("1 - Voulez-vous retrouvez les aliments substitués ?")
            print("2 - Quel aliment souhaitez-vous remplacer ?")

            r = input()

            if(r not in ["1", "2"]):
                print("Merci de taper la bonne valeur")
                r_correct = False
            else:
                r_correct = True

        if r == "1":
            self.display_table()

            print("Souhaitez-vous continuer ? (y/n)")
            
            b_correct = False

            while b_correct != True:
                b = input()
                if b in ["y", "n", "Y", "N", "Yes", "yes", "no", "No"]:
                    b_correct = True
                else:
                    print("Merci de taper la bonne valeur")

            if b not in ["y", "Y", "Yes", "yes"]:
                print("A bientôt")
                sys.exit(0)

    # Permet á l'utilisateur de saisir son profil
    def ask_taste(self):
        list_profil = ["Meats", "Veggie", "Cocoa", "Fruits"]
        print("Quel profil êtes vous ?")
        k = 0
        for profil in list_profil:
            k = k + 1
            print(str(k) + "- " + profil)
        # Permet de vérifier que le choix de l'utilisateur est valide
        profil_is_correct = False
        while not profil_is_correct:
            n = input()
            valid_input = range(1, len(list_profil) + 1)
            valid_input = [str(i)
                           for i in valid_input]  # comprehension de liste
            if n in valid_input:
                profil_is_correct = True
            else:
                print("Veuillez préciser votre profil")
        self.taste = Taste()
        # Permet de stocker le profil sélectionné
        self.taste.set_name_taste(list_profil[int(n) - 1])
        self.research1['taste'] = self.taste.name_taste
        self.research2['taste'] = self.taste.name_taste

    # Permet á l'utilisateur de saisir sa catégorie
    def ask_category(self):
        print("Quelle catégorie ?")
        list_category = self.taste.food_list
        i = 0
        for cat in list_category:
            i = i + 1
            print(str(i) + "-" + cat)
        # Permet de vérifier que le choix de l'utilisateur est valide
        category_is_correct = False
        while not category_is_correct:
            ncat = input()
            valid_input = range(1, len(list_category) + 1)
            # comprehension de liste : parcours d'une liste pour en générer une nouvelle, se repère á la présence de [... for ... in list]
            valid_input = [str(i) for i in valid_input]
            if ncat in valid_input:
                category_is_correct = True
            else:
                print("Veuillez préciser votre catégorie")
        # l'utilisateur compte á partir de 1 alors que Python á partir de 0
        selected_category = list_category[int(ncat) - 1]
        self.research1['category'] = selected_category
        self.research2['category'] = selected_category
        return selected_category

    # Permet á l'utilisateur de choisir un produit
    def ask_product(self, category):
        # Génère la première page
        category = category.replace(" ", "%20")
        with urllib.request.urlopen("https://world.openfoodfacts.org/cgi/search.pl?search_terms=" + category + "&json=1") as url:
            s = url.read()
        result = json.loads(s.decode("utf-8"))["products"][0:50]
        k = 0
        print("Quel produit ?")
        for product in result:
            k = k + 1
            if ('\u0153' in product['product_name']):
                print(str(k) + "-" +
                      product['product_name'].replace('\u0153', 'oe'))
            else:
                print(str(k) + "-" + product['product_name'])
        n_product = get_validated_input(result, "produit")
        print(n_product)
        selected_product = result[int(n_product) - 1]

        # Stocke le nom du produit de départ et son URL
        self.research1['product_name'] = selected_product['product_name']
        self.research1['url'] = selected_product['url']

        # Affiche le tableau de sélection
        ingredients = selected_product['ingredients']
        df = pd.DataFrame(ingredients)
        print(df[['text', 'rank']][0:10])
        return(result, n_product)

    def ask_ingredients(self, result, n_product):
        ingredients = result[int(n_product) - 1]['ingredients']
        df = pd.DataFrame(ingredients)
        print("Quel ingrédients souhaitez-vous substituer ? (rank)")
        n_ingredient = get_validated_input(ingredients, "ingredient")
        n_ingredient = int(n_ingredient)
        name_ingredient = list(df[['text']].loc[n_ingredient - 1])[0]
        print("Vous avez choisi de remplacer l'ingrédient " + name_ingredient)
        return name_ingredient

    def change(self, result, list_name_ingredient):
        self.list_avoid.append(list_name_ingredient)
        index = 0
        boolean_found_product = False
        while boolean_found_product == False and index < len(result):
            ingredient = result[index]['ingredients']
            list_ingredients = []
            for i in range(len(ingredient)):
                list_ingredients.append(ingredient[i]['text'])
            # Utilisation de Set pour comparer les "ensembles" d'ingrédients
            A = set(list_ingredients)
            B = set(self.list_avoid)
            if (len(A - B) == len(A)):
                # on peut en supprimant cette ligne parcourir toute la liste et proposer plusieurs choix
                boolean_found_product = True
                if ('\u0153' in result[index]['product_name']):
                    print("Le produit de substitution est : " +
                          result[index]['product_name'].replace('\u0153', 'oe'))
                else:
                    print("Le produit de substitution est : " +
                          result[index]['product_name'])
                n_product = index
            index = index + 1
        return n_product

    # Fonction principale relancée par procress()
    def process_one_try(self):
        self.ask_taste()
        category = self.ask_category()
        result, n_product = self.ask_product(category)
        print('Souhaitez-vous vous arrêter lá ? (taper 1), Souhaitez-vous changer de produit ? (taper 2)')
        choice = get_validated_input([1, 2], "option")
        if(choice == "1"):
            print(result[int(n_product) - 1]['stores'] + ' - ' +
                  result[int(n_product) - 1]['purchase_places'])
        else:
            list_name_ingredient = self.ask_ingredients(result, n_product)
            boolean_last_change = 0
            while boolean_last_change < 5:
                print(
                    'Souhaitez-vous vous arrêter lá ? (taper 1), Souhaitez-vous changer de produit ? (taper 2)')
                choice = get_validated_input([1, 2], "option")
                if(choice == "1"):
                    print(result[int(n_product) - 1]['stores'] + ' - ' +
                          result[int(n_product) - 1]['purchase_places'])
                    break
                n_product = self.change(result, list_name_ingredient)
                ingredients = result[int(n_product) - 1]['ingredients']
                df = pd.DataFrame(ingredients)
                print(df[['text', 'rank']][0:10])
                list_name_ingredient = self.ask_ingredients(
                    result, n_product - 1)
                # commenter cette ligne (#) pour une infinit├® d'it├®ration
                boolean_last_change += 1
        selected_product = result[int(n_product) - 1]

        # Stocke les informations du produit d'arrivée
        self.research2['product_name'] = selected_product['product_name']
        self.research2['stores'] = selected_product['stores']
        self.research2['purchase_places'] = selected_product['purchase_places']
        self.research2['url'] = selected_product['url']

        print("Produit de départ", self.research1['product_name'])
        print("Produit d'arrivée", self.research2['product_name'])
        try:
            ### Stockage des données ###
            # Connexion á la BDD
            conn = sqlite3.connect("foody.db")
            cursor = conn.cursor()

            # Remplissage données vides
            self.research1["stores"] = None
            self.research1["purchase_places"] = None

            # Insertion de données
            cursor.execute(
                """INSERT INTO Historic (taste, category, product_name, stores, purchase_places, url) VALUES(:taste, :category, :product_name, :stores, :purchase_places, :url)""", self.research1)
            cursor.execute(
                """INSERT INTO Historic (taste, category, product_name, stores, purchase_places, url) VALUES(:taste, :category, :product_name, :stores, :purchase_places, :url)""", self.research2)
            conn.commit()

            # Fermeture de la connexion
            conn.close()
        except ValueError:
            print("Erreur de base de donn├®es")
        return(self.research1, self.research2)

    # Fonction de lancement et de gestion de la répétition
    def process(self):
        self.first()
        try_again = True
        while try_again:
            r1, r2 = self.process_one_try()
            print("Souhaitez-vous effectuer une nouvelle requête ?")
            is_correct = False
            while not is_correct:
                n = input()
                valid_input = ["y", "n"]
                if n in valid_input:
                    is_correct = True
                else:
                    print("Veuillez préciser votre choix.")
            if n == "n":
                try_again = False
        print("A bient├┤t")
        return r1, r2

    # Permet d'afficher le contenu des requêtes précédentes
    def display_table(self):
        ### Stockage des données ###
        # Connexion ├á la BDD
        conn = sqlite3.connect("foody.db")
        cursor = conn.cursor()
        # Lire l'historique
        cursor.execute(
            """SELECT * FROM historic""")
        self.historic = cursor.fetchall()

        # Fermeture de la connexion
        conn.close()
        self.historic = pd.DataFrame(self.historic)
        if self.historic.shape[0] != 0:
            self.historic = self.historic.set_index(0)
            self.historic.columns = [
                "Taste", "Category", "Selected product", "Stores", "Purchase places", "URL"]
            print(self.historic)
    # Fonction de recherche dans la table

    def research(self):
        list_columns = ["Category", "Selected product", "Stores"]
        col_mysql = ["category", "product_name", "stores"]

        i = 0
        print("Veuillez choisir un champ de recherche")
        for col in list_columns:
            i = i + 1
            print(str(i) + "-" + col)
        selected_column = get_validated_input(
            list_columns, "champ de recherche")
        col_validated = col_mysql[int(selected_column) - 1]
        text_research = input()
        conn = sqlite3.connect("foody.db")
        cursor = conn.cursor()
        print("SELECT * FROM historic WHERE {} LIKE '%{}%'".format(col_validated, text_research))
        cursor.execute(
            "SELECT * FROM historic WHERE {} LIKE '%{}%'".format(col_validated, text_research))

        rows = cursor.fetchall()
        print(pd.DataFrame(rows))
        return pd.DataFrame(rows)



def get_validated_input(list_inputs, input_name):
    """
    input
     * list_inputs - liste des valeurs valides
     * input_name - cha├«ne de caract├¿re qui repr├®sente la valeur s├®lectionn├®e
    output
     * n - cha├«ne de caract├¿re entr├®e par l'utilisateur
     Fonction validant la saisie d'un utilisateur
    """
    is_correct = False
    while not is_correct:
        n = input()
        valid_input = range(1, len(list_inputs) + 1)
        valid_input = [str(i) for i in valid_input]  # comprehension de liste
        if n in valid_input:
            is_correct = True
        else:
            print("Veuillez préciser votre " + input_name)
    return n




help(get_validated_input)




Phil = Persona()
r1, r2 = Phil.process()

Phil.display_table()
df = Phil.research()





Phil = Persona()
df = Phil.research()