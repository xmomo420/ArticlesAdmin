import hashlib
import sqlite3


class Article:
    def __init__(self, identifiant, titre, auteur, date, contenu, est_html):
        self.identifiant = identifiant
        self.titre = titre
        self.auteur = auteur
        self.date = date
        self.contenu = contenu
        self.est_html = est_html


class Utilisateur:
    def __init__(self, id_utilisateur, prenom, nom, identifiant, courriel, photo):
        self.id_utilisateur = id_utilisateur
        self.prenom = prenom
        self.nom = nom
        self.identifiant = identifiant
        self.courriel = courriel
        self.photo = photo


class Database():

    # Structures de données pour modéliser la base de données

    def __init__(self):
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect('db/database.db')
        return self.connection

    def deconnection(self):
        if self.connection is not None:
            self.connection.close()

    def ajouter_utilisateur(self, prenom, nom, identifiant, courriel, hach, salt, photo):
        photo_binaire = sqlite3.Binary(photo.read())
        connection = self.get_connection()
        connection.execute(
            "INSERT INTO utilisateur (prenom, nom, identifiant, courriel, hach, salt, photo_profil) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (prenom, nom, identifiant, courriel, hach, salt, photo_binaire))
        connection.commit()

    def get_article(self, identifiant):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM article WHERE identifiant = ?", (identifiant,))
        resultat = cursor.fetchone()
        if resultat:
            return Article(identifiant=resultat[0], titre=resultat[1], auteur=resultat[2],
                           date=resultat[3], contenu=resultat[4], est_html=resultat[5])
        else:
            return None

    def get_photo_auteur(self, auteur_id):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM utilisateur WHERE id = ?", (auteur_id,))
        resultat = cursor.fetchone()
        return resultat[7]

    def get_5_premiers_articles(self):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM article")
        articles = cursor.fetchall()
        # Boucler pour remplir une liste d'article
        return articles

    def get_all_utilisateurs(self):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM utilisateur")
        utilisateurs = cursor.fetchall()
        liste_utilisateurs = []
        # TODO : Boucler pour remplir une liste d'utilisateur
        for utilisateur in utilisateurs:
            liste_utilisateurs.append(Utilisateur(id_utilisateur=utilisateur[0], prenom=utilisateur[1],
                                                  nom=utilisateur[2], identifiant=utilisateur[3],
                                                  courriel=utilisateur[4], photo=utilisateur[7]))
        return liste_utilisateurs

    def authentifier(self, identifiant, mot_de_passe):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM utilisateur WHERE identifiant = ?", (identifiant,))
        utilisateur = cursor.fetchone()
        if utilisateur:  # Si l'utilisateur existe
            hashed_db = utilisateur[5]
            salt = utilisateur[6]
            # Si le mot de passe correspond
            if hashed_db == hashlib.sha512(str(mot_de_passe + salt).encode("utf-8")).hexdigest():
                return utilisateur[0]
            else:
                return None
        else:
            return None

    def creer_session(self, id_session, id_utilisateur):
        connection = self.get_connection()
        connection.execute("INSERT INTO session "
                           "(id_session, utilisateur) VALUES (?, ?)", (id_session, id_utilisateur))
        connection.commit()

    def supprimer_session(self, id_session):
        connection = self.get_connection()
        connection.execute("DELETE FROM session WHERE id_session = ?", (id_session,))
        connection.commit()

    def get_session(self, id_session):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM session WHERE id_session = ?", (id_session,))
        donnee = cursor.fetchone()
        return donnee[0]

    def get_utilisateur(self, id_utilisateur):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM utilisateur WHERE id = ?", (id_utilisateur,))
        utilisateur = cursor.fetchone()
        if utilisateur:
            return Utilisateur(id_utilisateur=utilisateur[0], prenom=utilisateur[1], nom=utilisateur[2],
                               identifiant=utilisateur[3],courriel=utilisateur[4], photo=utilisateur[7])
        else:
            return None
