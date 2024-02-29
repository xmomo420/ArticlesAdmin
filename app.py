import base64

from flask import Flask, render_template, request, redirect, url_for, g, session, abort
from database import Database
from datetime import date
import hashlib
import uuid
import secrets
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = secrets.token_hex(16)

# Constantes

MESSAGE_404 = "La ressource à laquelle vous avez tentée d'accéder n'existe pas."


# Fonctions liées à la base de données
def get_db():
    database = getattr(g, '_database', None)
    if database is None:
        g._database = Database()
    return g._database


def deconnection():
    database = getattr(g, '_database', None)
    if database is not None:
        database.deconnection()


# Routes

@app.route('/', methods=['GET'])
def index():
    message_logout = request.args.get('message_logout', None)
    articles = get_db().get_5_premiers_articles()  # Récupérer les articles de la BD et les mettre dans une variable
    articles_tries = sorted(articles, key=lambda un_article: un_article.date, reverse=True)  # Trier selon la date
    return render_template('index.html', nom='Accueil', liste=articles_tries[:5], message_logout=message_logout), 200


@app.route('/article/<identifiant>', methods=['GET'])
def article(identifiant):
    identifiant_db = get_db().get_article(identifiant)
    if identifiant_db is not None:  # Si l'identifiant existe dans la BD
        photo = identifiant_db.get_photo(identifiant_db.auteur_id)
        render_template('article.html', nom='Article', identifiant=identifiant_db), 200
    else:
        return 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        message = request.args.get('message', None)
        return render_template('login.html', nom_page='Authentification', message=message), 200
    else:  # méthode POST : Formulaire envoyé
        mot_de_passe = request.form['mot_de_passe']
        identifiant = request.form['identifiant']
        id_utilisateur = get_db().authentifier(identifiant, mot_de_passe)
        if id_utilisateur is not None:  # Authentification réussi
            # Code pour ajouter l'utilisateur à la session
            id_session = uuid.uuid4().hex
            get_db().creer_session(id_session, id_utilisateur)
            session['id_session'] = id_session
            session['id_utilisateur'] = id_utilisateur
            return redirect(url_for('admin'), 302)
        else:
            message = "Combinaison courriel et mot de passe invalide"
            return render_template('login.html', nom_page='Authentification', message=message), 200


# Gestion de la session en cours
def est_authentifie():
    if 'id_session' in session:
        id_session_db = get_db().get_session(session['id_session'])
        return id_session_db is not None


def authentification_requise(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not est_authentifie():
            message = "Vous devez d'abord vous authentifier"
            return redirect(url_for('login', message=message), 302)
        return f(*args, **kwargs)

    return decorated


@app.route('/admin', methods=['GET'])
@authentification_requise
def admin():
    return render_template('admin.html', nom_page='Administration'), 200


@app.route('/utilisateur', methods=['GET'])
@authentification_requise
def utilisateur():
    liste_utilisateurs = get_db().get_all_utilisateurs()
    message = request.args.get('message', None)
    return render_template('utilisateur.html', nom_page='Utilisateurs', liste=liste_utilisateurs,
                           message=message), 200


@app.route('/utilisateur/ajouter', methods=['GET', 'POST'])
@authentification_requise
def ajouter_utilisateur():
    if request.method == 'GET':
        message = request.args.get('message', None)
        return render_template('ajouter_utilisateur.html', nom_page='Ajout nouvel utilisateur',
                               message=message), 200
    else:  # POST
        prenom = request.form['prenom']
        nom = request.form['nom']
        identifiant = request.form['identifiant']
        courriel = request.form['courriel']
        validation_courriel = request.form['confirmation_courriel']
        mot_de_passe = request.form['mot_de_passe']
        photo = None
        if 'photo' in request.files:
            photo = request.files['photo']
        # TODO : Valider le formulaire
        # TODO : Si tout est valide
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512(str(mot_de_passe + salt).encode("utf-8")).hexdigest()
        get_db().ajouter_utilisateur(prenom, nom, identifiant, courriel, hashed_password, salt, photo)
        message = f"L'utilisateur {prenom} {nom} a été ajouté avec succès"
        return redirect(url_for('ajouter_utilisateur', message=message), 302)


@app.route('/utilisateur/supprimer', methods=['POST'])
@authentification_requise
def supprimer_utilisateur():
    id_utilisateur = request.form['id_utilisateur']
    # TODO : Désactiver l'utilisateur de la BD
    message = f"L'utilisateur a été désactivé avec succès"
    return redirect(url_for('utilisateur', message=message), 302)


@app.route('/utilisateur/modifier', methods=['GET', 'POST'])
@authentification_requise
def modifier_utilisateur():
    if request.method == 'GET':
        id_utilisateur = request.args.get('id_utilisateur')
        message = request.args.get('message', None)
        if id_utilisateur:
            utilisateur_modifie = get_db().get_utilisateur(id_utilisateur)
            photo_b64 = base64.b64encode(utilisateur_modifie.photo).decode('utf-8')  # Récupérer la photo
            return render_template('modifier.html', nom_page="Modification utilisateur",
                                   prenom=utilisateur_modifie.prenom, nom=utilisateur_modifie.nom,
                                   courriel=utilisateur_modifie.courriel, photo=photo_b64,
                                   identifiant=utilisateur_modifie.identifiant, message=message), 200
    else:
        # TODO : Valider le formulaire
        message = "L'utilisateur a été modifié"
        return redirect(url_for('utilisateur', message=message), 302)


@app.route('/profil')
@authentification_requise
def profil():
    # Code pour récupérer les données de l'utilisateur connecté
    utilisateur_connecte = get_db().get_utilisateur(session['id_utilisateur'])
    prenom = utilisateur_connecte.prenom
    nom = utilisateur_connecte.nom
    identifiant = utilisateur_connecte.identifiant
    courriel = utilisateur_connecte.courriel
    photo = utilisateur_connecte.photo
    photo_b64 = base64.b64encode(photo).decode('utf-8')
    # TODO : Extraire la photo de 'utilisateur_connecte' et la passer en paramètre à la réponse
    return render_template('profil.html', nom_page='Profil', prenom=prenom, nom=nom,
                           identifiant=identifiant, courriel=courriel, photo=photo_b64)


@app.route('/logout')
@authentification_requise
def logout():
    id_session = session['id_session']
    session.pop('id_session', None)
    session.pop('id_utilisateur', None)
    get_db().supprimer_session(id_session)
    message_logout = "Vous avez été déconnecté avec succès"
    return redirect(url_for('index', message_logout=message_logout), 302)


# Gestion des erreurs

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', message=MESSAGE_404), 404


if __name__ == '__main__':
    app.run()
