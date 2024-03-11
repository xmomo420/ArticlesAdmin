from flask import (Flask, render_template, request, redirect, url_for, g,
                   session, abort)

from database import Database
from datetime import datetime
import base64
import hashlib
import uuid
import secrets
import re
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = secrets.token_hex(16)


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


@app.route('/', methods=['GET'])
def index():
    message_logout = request.args.get('message_logout', None)
    message_desactivation = request.args.get('message_desactivation', None)
    articles = get_db().get_all_articles()
    if articles is not None:
        # Trier selon la date
        articles = sorted(articles, key=lambda un_article: un_article.date,
                          reverse=True)
        articles = articles[:5]
    # Ajoutez le nom de l'auteur à chaque article
    for article in articles:
        article.nom_auteur = get_db().get_nom_auteur(article.auteur)
    return render_template('index.html', nom_page='Accueil',
                           liste=articles, message_logout=message_logout,
                           message_desactivation=message_desactivation), 200


@app.route('/article/<identifiant>', methods=['GET'])
def article(identifiant):
    article = get_db().get_article(identifiant)
    if article is not None:  # Si l'identifiant existe dans la BD
        photo = get_db().get_photo_auteur(article.auteur)
        photo_b64 = base64.b64encode(photo).decode('utf-8')
        nom_complet = get_db().get_nom_auteur(article.auteur)
        return render_template('article.html',
                               nom_page='Article', identifiant=article,
                               photo=photo_b64, nom_complet=nom_complet,
                               article=article), 200
    else:
        abort(404)


@app.route('/recherche', methods=['POST'])
def recherche():
    patron_recherche = request.form['recherche']
    articles = get_db().get_articles_like(patron_recherche)
    message = None
    if articles is None:
        message = "Aucun résultat ne correspond à votre recherche"
    return (
        render_template('recherche.html',
                        nom_page='Recherche', liste=articles, message=message,
                        recherche=patron_recherche), 200)


@app.route('/login', methods=['GET'])
def login():
    if request.method == 'GET':
        message = request.args.get('message', None)
        return (render_template('login.html',
                                nom_page='Authentification', message=message),
                200)


@app.route('/login/traitement', methods=['POST'])
def traitement_login():
    mot_de_passe = request.form['mot_de_passe']
    identifiant = request.form['identifiant']
    id_utilisateur = get_db().authentifier(identifiant, mot_de_passe)
    if id_utilisateur is not None:  # Utilisateur existant
        if get_db().get_utilisateur(
                id_utilisateur).actif == 0:
            message = 'Cet utilisateur a été désactivé'
            return redirect(url_for('login', message=message), 302)
        else:  # Utilisateur actif
            # Code pour ajouter l'utilisateur à la session
            id_session = uuid.uuid4().hex
            get_db().creer_session(id_session, id_utilisateur)
            session['id_session'] = id_session
            session['id_utilisateur'] = id_utilisateur
            return redirect(url_for('admin'), 302)
    else:
        message = "Combinaison identifiant et mot de passe invalide"
        return redirect(url_for('login', message=message), 302)


@app.route('/admin', methods=['GET'])
@authentification_requise
def admin():
    liste_articles = get_db().get_all_articles()
    message = request.args.get('message', None)
    return render_template('admin.html',
                           nom_page='Administration', message=message,
                           liste=liste_articles), 200


@app.route('/admin-nouveau', methods=['GET'])
@authentification_requise
def admin_nouveau():
    # Variables représentant les critères de validation
    critere_titre = "Un titre ne doit pas être vide."
    critere_contenu = "Le contenu ne peut pas être vide."
    critere_est_html = "Vous devez séléctionner une des deux options."
    message = request.args.get('message', None)
    titre = request.args.get('titre', '')
    contenu = request.args.get('contenu', '')
    est_html = int(request.args.get('est_html', -1))
    if message is not None:  # Erreur lors de la validation du formulaire
        code = 400  # Mauvaise requête
    else:
        code = 200
    return render_template('admin-nouveau.html',
                           nom_page='Nouvel article', message=message,
                           critere_contenu=critere_contenu,
                           critere_titre=critere_titre,
                           critere_est_html=critere_est_html, titre=titre,
                           contenu=contenu, est_html=est_html), code


def formulaire_valide(titre, contenu, est_html):
    return titre.strip() != '' and contenu.strip() != '' and est_html != -1


def generer_identifiant_unique():
    id_trouve = False
    identifiant_unique = uuid.uuid4().hex
    while id_trouve is False:
        identifiant_unique = uuid.uuid4().hex
        id_trouve = get_db().get_article(identifiant_unique) is None
    return identifiant_unique


@app.route('/admin-nouveau/traitement', methods=['POST'])
@authentification_requise
def admin_nouveau_traitement():
    titre = request.form['titre']
    contenu = request.form['contenu']
    est_html = int(request.form.get('est_html', -1))
    if formulaire_valide(titre, contenu,
                         est_html):  # Si le formulaire est valide
        message = "L'article a été ajouté avec succès"
        # Ajouter la'rticle dans la base de données
        auteur = session['id_utilisateur']
        date_publiation = datetime.now()
        identifiant = generer_identifiant_unique()
        get_db().ajouter_article(identifiant, titre, auteur, date_publiation,
                                 contenu, est_html)
        return redirect(url_for('admin', message=message), 302)
    else:  # Formulaire n'est pas valide
        message = ("Le forumulaire n'a pas été rempli correctement. Faites "
                   "attention aux critères pour chaque champs.")
        print(est_html)
        return redirect(url_for('admin_nouveau', message=message,
                                titre=titre, contenu=contenu,
                                est_html=est_html),
                        302)


@app.route('/admin/modifier/id=<identifiant>', methods=['GET'])
@authentification_requise
def admin_modifier(identifiant):
    article_modifie = get_db().get_article(identifiant)
    if article_modifie is not None:
        message = request.args.get('message', None)
        if message is not None:
            code = 400
        else:
            code = 200
        titre = article_modifie.titre
        contenu = article_modifie.contenu
        est_html = int(article_modifie.est_html)
        critere_titre = "Un titre ne doit pas être vide."
        critere_contenu = "Le contenu ne peut pas être vide."
        critere_est_html = "Vous devez séléctionner une des deux options."
        return render_template('admin-modifier.html',
                               nom_page='Modification article',
                               message=message,
                               critere_contenu=critere_contenu,
                               critere_titre=critere_titre,
                               identifiant=identifiant,
                               critere_est_html=critere_est_html, titre=titre,
                               contenu=contenu, est_html=est_html), code
    else:
        abort(404)


@app.route('/admin/modifier/id=<identifiant>/traitement', methods=['POST'])
@authentification_requise
def admin_modifier_traitement(identifiant):
    titre = request.form.get('titre', None)
    contenu = request.form.get('contenu', None)
    est_html = int(request.form.get('est_html', -1))
    if formulaire_valide(titre, contenu, est_html):
        message = f"L'article \"{titre}\" a été modifier avec succès"
        get_db().modifier_article(identifiant, titre, contenu, est_html)
        return redirect(url_for('admin', message=message), 302)
    else:
        message = ("Le forumulaire n'a pas été rempli correctement.\n"
                   "Faites attention aux critères pour chaque champs.")
        success = False
        return redirect(
            url_for('admin_modifier', identifiant=identifiant,
                    titre=titre, contenu=contenu, est_html=est_html,
                    message=message, success=success), 302)


@app.route('/utilisateurs', methods=['GET'])
@authentification_requise
def utilisateur():
    liste_utilisateurs = get_db().get_all_utilisateurs()
    message = request.args.get('message', None)
    return render_template('utilisateurs.html',
                           nom_page='Utilisateurs', liste=liste_utilisateurs,
                           message=message), 200


@app.route('/utilisateurs/ajouter', methods=['GET'])
@authentification_requise
def ajouter_utilisateur():
    prenom = request.args.get('prenom', "")
    nom = request.args.get('nom', "")
    identifiant = request.args.get('identifiant', "")
    courriel = request.args.get('courriel', "")
    list_username = get_db().get_all_usernames()
    message = request.args.get('message', None)
    if message is not None:
        code = 400
    else:
        code = 200
    return render_template('ajouter_utilisateur.html',
                           nom_page='Ajout nouvel utilisateur',
                           message=message, list_username=list_username,
                           prenom=prenom, nom=nom, identifiant=identifiant,
                           courriel=courriel), code


def valider_formulaire_ajout_utilisateur(prenom, nom, identifiant, courriel,
                                         confirmation_courriel, mot_de_passe,
                                         confirmation_mot_de_passe, photo):
    courriels_valides = (courriel.strip() != ''
                         and courriel.strip() == confirmation_courriel.strip())
    liste_identifiants = get_db().get_all_usernames()
    identifiant_valide = (identifiant.strip() not in liste_identifiants
                          and identifiant.strip() != '')
    photo_valide = photo.filename != ''
    mot_de_passe_valide = re.match(
        r'^(?=.*[!@#$%^&*\-,])(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$',
        mot_de_passe)
    mots_de_passe_valides = (mot_de_passe_valide
                             and mot_de_passe == confirmation_mot_de_passe)
    nom_valide = prenom.strip() != '' and nom.strip() != ''
    return (identifiant_valide and courriels_valides and nom_valide
            and photo_valide and mots_de_passe_valides)


@app.route('/utilisateurs/ajouter/traitement', methods=['POST'])
@authentification_requise
def utilisateur_ajouter_traitement():
    prenom = request.form['prenom']
    nom = request.form['nom']
    identifiant = request.form['identifiant']
    courriel = request.form['courriel']
    confirmation_courriel = request.form['confirmation_courriel']
    mot_de_passe = request.form['mot_de_passe']
    confirmation_mot_de_passe = request.form['confirmation_mot_de_passe']
    photo = request.files['photo']
    if valider_formulaire_ajout_utilisateur(prenom, nom, identifiant, courriel,
                                            confirmation_courriel,
                                            mot_de_passe,
                                            confirmation_mot_de_passe, photo):
        liste_courriels = get_db().get_all_courriels()
        if courriel not in liste_courriels:
            # Formulaire valide
            salt = uuid.uuid4().hex
            hashed_password = hashlib.sha512(
                str(mot_de_passe + salt).encode("utf-8")).hexdigest()
            get_db().ajouter_utilisateur(prenom.strip(), nom.strip(),
                                         identifiant.strip(), courriel.strip(),
                                         hashed_password, salt, photo)
            message = f"L'utilisateur {prenom} {nom} a été ajouté avec succès"
            return redirect(url_for('utilisateur', message=message),
                            302)
        else:
            message = (f"L'adresse courriel \"{courriel}\" a déjà été prise "
                       f"par un autre utilisateur")
            return redirect(
                url_for('ajouter_utilisateur', message=message,
                        prenom=prenom, nom=nom, identifiant=identifiant),
                302)
    else:
        message = 'Formulaire invalide, veuillez respecter tous les champs'
        return redirect(
            url_for('ajouter_utilisateur', message=message,
                    prenom=prenom, nom=nom, identifiant=identifiant,
                    courriel=courriel), 302)


@app.route('/utilisateurs/desactiver/<id_utilisateur>')
@authentification_requise
def desactiver_utilisateur(id_utilisateur):
    if get_db().get_utilisateur(id_utilisateur) is not None:
        get_db().desactiver_utilisateur(id_utilisateur)
        utilisateur = get_db().get_utilisateur(id_utilisateur)
        prenom = utilisateur.prenom
        nom = utilisateur.nom
        message = f"L'utilisateur {prenom} {nom} a été désactivé avec succès"
        if int(id_utilisateur) == int(session['id_utilisateur']):
            id_session = session['id_session']
            session.pop('id_session', None)
            session.pop('id_utilisateur', None)
            get_db().supprimer_session(id_session)
            message = "Vous n'êtes pas autorisé à accéder à ce contenu"
            return redirect(url_for('index',
                                    message_desactivation=message), 302)
        else:
            return redirect(url_for('utilisateur', message=message),
                            302)
    else:
        abort(404)


@app.route('/utilisateurs/modifier/id=<id_utilisateur>', methods=['GET'])
@authentification_requise
def modifier_utilisateur(id_utilisateur):
    utilisateur_modifie = get_db().get_utilisateur(id_utilisateur)
    if utilisateur_modifie is not None:
        liste_usernames = get_db().get_all_usernames()
        message = request.args.get('message', None)
        photo_b64 = base64.b64encode(utilisateur_modifie.photo).decode(
            'utf-8')  # Récupérer la photo
        return render_template('modifier.html',
                               nom_page="Modification utilisateur",
                               prenom=utilisateur_modifie.prenom,
                               nom=utilisateur_modifie.nom,
                               courriel=utilisateur_modifie.courriel,
                               photo=photo_b64,
                               identifiant=utilisateur_modifie.identifiant,
                               message=message,
                               liste_usernames=liste_usernames,
                               actif=utilisateur_modifie.actif,
                               id_utilisateur=id_utilisateur), 200
    else:
        abort(404)


def valider_formulaire_modification_utilisateur(prenom, nom, identifiant,
                                                courriel,
                                                confirmation_courriel, statut,
                                                id_utilisateur):
    liste_usernames = get_db().get_all_usernames()
    utilisateur_modifie = get_db().get_utilisateur(id_utilisateur)
    identifiant_valide = (identifiant not in liste_usernames
                          or identifiant == utilisateur_modifie.identifiant)
    courriel_identiques = courriel.strip() == confirmation_courriel.strip()
    statut_valide = statut == 0 or statut == 1
    if identifiant_valide and courriel_identiques and statut_valide:
        champs = [prenom, nom, identifiant, courriel]
        return all(champ.strip() != '' for champ in champs)
    else:
        return False


def verifier_unicite_courriel(courriel, id_utilisateur):
    liste_courriels = get_db().get_all_courriels()
    courriel_courrant = get_db().get_utilisateur(id_utilisateur).courriel
    return courriel not in liste_courriels or courriel == courriel_courrant


@app.route('/utilisateurs/modifier/id=<id_utilisateur>/traitement',
           methods=['POST'])
@authentification_requise
def utilisateur_modifier_traitement(id_utilisateur):
    prenom = request.form['prenom']
    nom = request.form['nom']
    identifiant = request.form['identifiant']
    courriel = request.form['courriel']
    confirmation_courriel = request.form['confirmation_courriel']
    statut = int(request.form['statut'])
    photo = request.files['photo']
    if photo.filename == '':
        photo = None
    if valider_formulaire_modification_utilisateur(prenom, nom, identifiant,
                                                   courriel,
                                                   confirmation_courriel,
                                                   statut,
                                                   id_utilisateur):
        if verifier_unicite_courriel(courriel,
                                     id_utilisateur):  # Formulaire valide
            get_db().modifier_utilisateur(prenom.strip(), nom.strip(),
                                          identifiant.strip(),
                                          courriel.strip(), photo, statut,
                                          id_utilisateur)
            message = (f"L'utilisateur \"{identifiant}\" a été modifié avec "
                       f"succès")
            endpoint = 'utilisateur'
        else:
            message = (f"L'adresse courriel \"{courriel}\" a déja été prise "
                       f"par un autre utilisateur")
            endpoint = 'modifier_utilisateur'
    else:
        message = "Le formulaire n'a pas été rempli correctement"
        endpoint = 'modifier_utilisateur'
    return redirect(url_for(endpoint=endpoint, id_utilisateur=id_utilisateur,
                            message=message), 302)


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
    return render_template('profil.html', nom_page='Profil',
                           prenom=prenom, nom=nom, identifiant=identifiant,
                           courriel=courriel, photo=photo_b64)


@app.route('/logout')
@authentification_requise
def logout():
    id_session = session['id_session']
    session.pop('id_session', None)
    session.pop('id_utilisateur', None)
    get_db().supprimer_session(id_session)
    message_logout = "Vous avez été déconnecté avec succès"
    return redirect(url_for('index', message_logout=message_logout),
                    302)


# Gestion des erreurs

MESSAGE_404 = "La ressource à laquelle vous avez tentée d'accéder n'existe pas"
MESSAGE_405 = ("La méthode que vous avez utilisée n'est pas permise pour cette"
               "requête")
MESSAGE_500 = ("Une erreur est survenu dans le côté du serveur et n'a pas pu "
               "complété votre requête")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('erreur.html', message=MESSAGE_404,
                           titre="Erreur 404"), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return render_template('erreur.html', message=MESSAGE_405,
                           titre="Erreur 405"), 405


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('erreur.html', message=MESSAGE_500,
                           titre="Erreur 500"), 500


if __name__ == '__main__':
    app.run()
