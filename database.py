import hashlib
import sqlite3
from datetime import datetime


class Article:
    def __init__(self, identifiant, titre, auteur, date, contenu, est_html):
        self.identifiant = identifiant
        self.titre = titre
        self.auteur = auteur
        self.date = date
        self.contenu = contenu
        self.est_html = est_html


class Utilisateur:
    def __init__(self, id_utilisateur, prenom, nom, identifiant, courriel, photo, actif):
        self.id_utilisateur = id_utilisateur
        self.prenom = prenom
        self.nom = nom
        self.identifiant = identifiant
        self.courriel = courriel
        self.photo = photo
        self.actif = actif


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
            "INSERT INTO utilisateur (prenom, nom, identifiant, courriel, hach, salt, photo_profil, actif) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
            (prenom, nom, identifiant, courriel, hach, salt, photo_binaire))
        connection.commit()

    def ajouter_article(self, identifiant, titre, auteur_id, date, contenu, est_html):
        connection = self.get_connection()
        connection.execute("INSERT INTO article (identifiant, titre, auteur_id, date_publication, contenu, est_html) "
                           "VALUES (?, ?, ?, ?, ?, ?)", (identifiant, titre, auteur_id, date, contenu, est_html))
        connection.commit()

    def get_article(self, identifiant):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM article WHERE identifiant == ?", (identifiant,))
        resultat = cursor.fetchone()
        if resultat:
            date = datetime.strptime(resultat[3], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d - %H:%M")
            return Article(identifiant=resultat[0], titre=resultat[1], auteur=resultat[2],
                           date=date, contenu=resultat[4], est_html=resultat[5])
        else:
            return None

    def get_photo_auteur(self, auteur_id):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT photo_profil FROM utilisateur WHERE id = ?", (auteur_id,))
        resultat = cursor.fetchone()
        return resultat[0]

    def get_nom_auteur(self, auteur_id):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT prenom || ' ' || nom AS nom_complet FROM utilisateur WHERE id = ?",
                       (auteur_id,))
        nom_complet = cursor.fetchone()
        return nom_complet[0]

    def get_all_articles(self):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM article")
        articles = cursor.fetchall()
        if len(articles) != 0:
            liste_articles = []
            # Boucler pour remplir une liste d'article
            for article in articles:
                # TODO : Transformer article[3] en date dont le format est celui qu'on veut
                date_formatee = datetime.strptime(article[3], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d - %H:%M")
                liste_articles.append(
                    Article(identifiant=article[0], titre=article[1], auteur=article[2], date=date_formatee,
                            contenu=article[4], est_html=article[5]))
            return liste_articles

    def get_articles_like(self, recherche):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM article WHERE titre LIKE ? OR contenu LIKE ?",
                       ('%' + recherche + '%', '%' + recherche + '%'))
        articles = cursor.fetchall()
        if len(articles) != 0:
            liste_articles = []
            for article in articles:
                date_formatee = datetime.strptime(article[3], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d - %H:%M")
                liste_articles.append(
                    Article(identifiant=article[0], titre=article[1], auteur=article[2], date=date_formatee,
                            contenu=article[4], est_html=article[5]))
            return liste_articles
        else:
            return None

    def get_all_utilisateurs(self):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM utilisateur")
        utilisateurs = cursor.fetchall()
        liste_utilisateurs = []
        # TODO : Boucler pour remplir une liste d'utilisateur
        for utilisateur in utilisateurs:
            liste_utilisateurs.append(Utilisateur(id_utilisateur=utilisateur[0], prenom=utilisateur[1],
                                                  nom=utilisateur[2], identifiant=utilisateur[3],
                                                  courriel=utilisateur[4], photo=utilisateur[7], actif=utilisateur[8]))
        return liste_utilisateurs

    def get_all_usernames(self):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT identifiant FROM utilisateur")
        usernames = cursor.fetchall()
        liste_usernames = []
        for username in usernames:
            liste_usernames.append(username[0])
        return liste_usernames

    def get_all_courriels(self):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT courriel FROM utilisateur")
        courriels = cursor.fetchall()
        liste_courriels = []
        for courriel in courriels:
            liste_courriels.append(courriel[0])
        return liste_courriels

    def get_all_articles_id(self):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT identifiant FROM article")
        identifiants = cursor.fetchall()
        liste_identifiants = []
        for identifiant in identifiants:
            liste_identifiants.append(identifiant)
        return liste_identifiants

    def authentifier(self, identifiant, mot_de_passe):
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT * FROM utilisateur WHERE identifiant == ?", (identifiant,))
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
                               identifiant=utilisateur[3], courriel=utilisateur[4], photo=utilisateur[7],
                               actif=utilisateur[8])
        else:
            return None

    def desactiver_utilisateur(self, id_utilisateur):
        connection = self.get_connection()
        connection.execute("UPDATE utilisateur SET actif = 0 WHERE id = ?", (id_utilisateur,))
        connection.commit()

    def modifier_article(self, identifiant, titre, contenu, est_html):
        connection = self.get_connection()
        connection.execute("UPDATE article SET titre = ?, contenu = ?, est_html = ? WHERE identifiant = ?",
                           (titre, contenu, est_html, identifiant))
        connection.commit()

    def modifier_utilisateur(self, prenom, nom, identifiant, courriel, photo, statut, id_utilisateur):
        connection = self.get_connection()
        if photo is not None:
            connection.execute("UPDATE utilisateur SET prenom = ?, nom = ?, identifiant = ?, courriel = ?, "
                               "photo_profil = ?, actif = ? WHERE id = ?", (prenom, nom, identifiant, courriel,
                                                                            sqlite3.Binary(photo.read()), statut,
                                                                            id_utilisateur))
        else:
            connection.execute("UPDATE utilisateur SET prenom = ?, nom = ?, identifiant = ?, courriel = ?, actif = ?"
                               " WHERE id = ?", (prenom, nom, identifiant, courriel, statut, id_utilisateur))
        connection.commit()
