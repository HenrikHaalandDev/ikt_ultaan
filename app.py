from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from functools import wraps
from sqlalchemy import func
from sqlalchemy.orm import relationship


# --- timezone (safe) ---
try:
    from zoneinfo import ZoneInfo
    OSLO_TZ = ZoneInfo("Europe/Oslo")
    UTC_TZ = ZoneInfo("UTC")
except Exception:
    # If tzdata is missing, ZoneInfo("Europe/Oslo") fails on some systems.
    OSLO_TZ = None
    UTC_TZ = None


# -------------------- APP CONFIG --------------------

app = Flask(__name__)

# Secrets
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "FYS8gh49g4jgjS6h4hG4sjg4g4g4")
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv("WTF_CSRF_SECRET_KEY", "g8GJg48gjGjg48gj48jg93jg")

# --- Database setup (Render + local) ---
# On Render: uses DATABASE_URL (Postgres)
# Locally: falls back to SQLite file loan_system.db
db_url = os.getenv("DATABASE_URL", "sqlite:///loan_system.db")

# If Render gives postgres://, convert to postgresql:// for SQLAlchemy
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)


# -------------------- TRANSLATIONS --------------------

# Vi bruker norsk tekst som nøkkel, og oversetter til engelsk når lang=en.
translations = {
    "en": {
        # App / felles
        "IKT Utlånssystem": "ICT Loan System",
        "Dashboard": "Dashboard",
        "PC-oversikt": "PC inventory",
        "Nytt utlån": "New loan",
        "Admin panel": "Admin panel",
        "Admin": "Admin",
        "Meny": "Menu",
        "Konto": "Account",
        "Min profil": "My profile",
        "Logg ut": "Log out",
        "Logget inn som": "Logged in as",

        # Login
        "Logg inn": "Log in",
        "Brukernavn": "Username",
        "Passord": "Password",

        # Flash-meldinger (de statiske)
        "Du må logge inn først.": "You must log in first.",
        "Administrator-tilgang kreves.": "Administrator access required.",
        "Innlogging vellykket.": "Login successful.",
        "Ugyldig brukernavn eller passord.": "Invalid username or password.",
        "Du er nå logget ut.": "You are now logged out.",
        "Ugyldig frist-dato. Bruk format ÅÅÅÅ-MM-DD.": "Invalid due date. Use format YYYY-MM-DD.",
        "Navn og utstyr er påkrevd.": "Name and item are required.",
        "Denne PC-en er allerede utlånt.": "This PC is already loaned out.",
        "Utlån registrert.": "Loan registered.",
        "Du har ikke tilgang til å se dette utlånet.": "You do not have permission to view this loan.",
        "Du har ikke tilgang til å returnere dette utlånet.": "You do not have permission to return this loan.",
        "Dette utlånet er allerede markert som returnert.": "This loan is already marked as returned.",
        "Utlånet er markert som returnert.": "The loan has been marked as returned.",
        "Utlånet ble slettet.": "The loan was deleted.",
        "Du har ikke tilgang til å endre dette utlånet.": "You do not have permission to edit this loan.",
        "OK-nummer og modelltype er påkrevd.": "OK number and model type are required.",
        "Denne PC-en finnes allerede.": "This PC already exists.",
        "PC lagt til i oversikten.": "PC added to inventory.",
        "Brukernavn og passord er påkrevd.": "Username and password are required.",
        "Brukernavnet er allerede i bruk.": "The username is already taken.",
        "Bruker lagt til.": "User added.",
        "Du kan ikke fjerne admin-rettigheter fra din egen bruker.": "You cannot remove admin rights from your own user.",
        "Du kan ikke slette din egen bruker.": "You cannot delete your own user.",
        "Kan ikke slette bruker som har registrerte utlån.": "Cannot delete a user who has registered loans.",
        "Nåværende passord er feil.": "Current password is incorrect.",
        "Nytt passord og bekreftelse matcher ikke.": "New password and confirmation do not match.",
        "Profil oppdatert.": "Profile updated.",

        # Dashboard / oversikt
        "Utlån – oversikt": "Loans – overview",
        "Rask oversikt over aktive, forfalte og returnerte utlån.": "Quick overview of active, overdue and returned loans.",
        "Aktive utlån": "Active loans",
        "Utlån som ikke er returnert": "Loans not yet returned",
        "Forfalte utlån": "Overdue loans",
        "Frist passert": "Due date passed",
        "Ingen frist": "No due date",
        "Returnert i dag": "Returned today",
        "Registrert som returnert i dag": "Marked as returned today",
        "Totalt returnert": "Total returned",
        "Historikk": "History",
        "Returnerte": "Returned",

        "Søk": "Search",
        "Søk på navn, gruppe eller utstyr...": "Search by name, group or item...",
        "Vis bare mine utlån": "Show only my loans",
        "Vis kun forfalte (aktive)": "Show only overdue (active)",
        "Sorter:": "Sort:",

        "Utlånt – nyeste først": "Checked out – newest first",
        "Utlånt – eldste først": "Checked out – oldest first",
        "Frist – tidligst først": "Due date – earliest first",
        "Frist – senest først": "Due date – latest first",
        "Utstyr – A → Å": "Item – A → Z",
        "Utstyr – Å → A": "Item – Z → A",
        "PC – A → Å": "PC – A → Z",
        "PC – Å → A": "PC – Z → A",
        "Navn – A → Å": "Name – A → Z",
        "Navn – Å → A": "Name – Z → A",
        "Returnert – nyeste først": "Returned – newest first",
        "Returnert – eldste først": "Returned – oldest first",

        # Column headers
        "Navn": "Name",
        "Gruppe": "Group",
        "Telefon": "Phone",
        "Utstyr": "Item",
        "PC": "PC",
        "Utlånt": "Checked out",
        "Frist": "Due date",
        "Handlinger": "Actions",

        # Loan detail
        "Utlån detaljer": "Loan details",
        "Returnert": "Returned",
        "Aktiv": "Active",
        "Tilbake": "Back",
        "Rediger": "Edit",
        "Marker som returnert": "Mark as returned",
        "Slett utlån": "Delete loan",
        "Er du sikker på at du vil slette dette utlånet? Denne handlingen kan ikke angres.": "Are you sure you want to delete this loan? This action cannot be undone.",
        "Navn på elev/ansatt": "Name of student/employee",
        "Ikke angitt": "Not specified",
        "Telefon": "Phone",
        "Klikk nummeret for å ringe.": "Click the number to call.",
        "PC (fra oversikt)": "PC (from inventory)",
        "Ikke registrert": "Not registered",
        "Hva er utlånt": "What is loaned out",
        "Verdisak": "Value item",
        "Hvorfor": "Reason",
        "Utlånt dato/tid": "Checkout date/time",
        "Frist for innlevering": "Return deadline",
        "Returnert dato/tid": "Return date/time",
        "Ikke returnert ennå": "Not yet returned",
        "Registrert av:": "Registered by:",
        "Telefonnummer kopiert til utklippstavlen.": "Phone number copied to clipboard.",
        "Kunne ikke kopiere telefonnummer.": "Could not copy phone number.",

        # New loan
        "Nytt utlån": "New loan",
        "Navn på elev/ansatt *": "Name of student/employee *",
        "Klasse": "Class",
        "Telefon": "Phone",
        "f.eks. 999 99 999": "e.g. 999 99 999",
        "Hva er utlånt *": "What is loaned out *",
        "Velg PC (valgfritt)": "Select PC (optional)",
        "-- Ingen valgt --": "-- None selected --",
        "Verdisak": "Value item",
        "f.eks. 5000 kr": "e.g. 5000 NOK",
        "Hvorfor": "Reason",
        "Frist for innlevering": "Return deadline",
        "Avbryt": "Cancel",
        "Registrer utlån": "Register loan",
        "* Obligatoriske felt": "* Required fields",

        # PC inventory
        "PC-oversikt": "PC inventory",
        "Legg til PC": "Add PC",
        "Søk på OK-nummer/serienr eller modell...": "Search by OK number/serial or model...",
        "Sorter: Modell A → Z": "Sort: Model A → Z",
        "Sorter: Modell Z → A": "Sort: Model Z → A",
        "Sorter: OK-nummer høy → lav": "Sort: OK number high → low",
        "Sorter: OK-nummer lav → høy": "Sort: OK number low → high",
        "Sorter: Utlånt først": "Sort: Loaned out first",
        "Sorter: Ledig først": "Sort: Available first",
        "Tøm søk": "Clear search",
        "OK-nummer / Serienr": "OK number / Serial no.",
        "Modelltype": "Model type",
        "Status": "Status",
        "Utlånt til": "Loaned to",
        "Utlånt": "Loaned out",
        "Ledig": "Available",
        "Ingen treff.": "No results.",
        "Ingen PC-er registrert ennå.": "No PCs registered yet.",

        # Add PC / Edit PC
        "OK-nummer / serienummer *": "OK number / serial number *",
        "Modelltype *": "Model type *",
        "Notater": "Notes",
        "Lagre": "Save",
        "Rediger PC": "Edit PC",
        "PC oppdatert.": "PC updated.",
        "Kan ikke slette PC som er utlånt.": "Cannot delete a PC that is loaned out.",
        "Kan ikke slette PC som har historikk. Marker evt. som utgått i notater.":
            "Cannot delete a PC with history. Mark as retired in notes instead.",
        "PC slettet.": "PC deleted.",

        # Admin panel
        "Admin Panel": "Admin panel",
        "Legg til bruker": "Add user",
        "Brukeradministrasjon": "User administration",
        "ID": "ID",
        "Brukernavn": "Username",
        "Admin": "Admin",
        "Handlinger": "Actions",
        "Ja": "Yes",
        "Nei": "No",
        "Fjern admin": "Remove admin",
        "Gi admin": "Make admin",
        "Er du sikker på at du vil slette denne brukeren?": "Are you sure you want to delete this user?",
        "Din konto": "Your account",
        "Ingen brukere funnet.": "No users found.",

        # Profil
        "Min profil": "My profile",
        "Brukernavn *": "Username *",
        "Nåværende passord *": "Current password *",
        "Du må oppgi ditt nåværende passord for å bekrefte endringer.": "You must enter your current password to confirm changes.",
        "Nytt passord": "New password",
        "La feltet stå tomt hvis du ikke vil endre passord.": "Leave this field empty if you do not want to change your password.",
        "Bekreft nytt passord": "Confirm new password",
        "Brukertype:": "User type:",
        "Administrator": "Administrator",
        "Standard bruker": "Standard user",
        "Lagre endringer": "Save changes",

        # Statistikk
        "Statistikk": "Statistics",
        "Oversikt over bruk av utlånssystemet – mest lånte ting, klasser og utvikling over tid.": "Overview of system usage – most loaned items, classes and trend over time.",
        "Totalt utlån": "Total loans",
        "Registrerte utlån totalt": "Registered loans total",
        "Aktive": "Active",
        "Forfalte": "Overdue",
        "Frist er passert": "Due date passed",
        "Returnerte": "Returned",
        "Utlån som er avsluttet": "Loans that are finished",
        "Brukere og utstyr": "Borrowers and equipment",
        "Unike låntakere": "Unique borrowers",
        "Unike utstyrstyper": "Unique item types",
        "Basert på unike kombinasjoner av navn og utstyr registrert i utlånene.": "Based on unique combinations of name and item registered in the loans.",
        "Utlån per måned": "Loans per month",
        "Måned": "Month",
        "Antall utlån": "Number of loans",
        "Relativt": "Relative",
        "Ingen data tilgjengelig ennå.": "No data available yet.",
        "Mest utlånte ting": "Most loaned items",
        "Utstyr": "Item",
        "Klasser med flest utlån": "Classes with most loans",
        "Klasse": "Class",
        "Ingen utlån registrert ennå.": "No loans registered yet.",
        "Ingen klasser registrert på utlån ennå.": "No classes registered on loans yet.",


        "Lavt lager på utstyr": "Low stock on items",
        "Kun få igjen på lager:": "Only a few left in stock:",


        # Dynamic label value if ever needed
        "Ansatt": "Employee",
    }
}


def translate(text: str) -> str:
    """Simple i18n function: uses Norwegian as default source text."""
    lang = session.get("lang", "no")
    if lang == "en":
        return translations.get("en", {}).get(text, text)
    return text


# --------- DYNAMIC ITEM TRANSLATION (e.g. 'lader' -> 'Charger') ---------

item_translations_en = {
    "lader": "Charger",
    "Lader": "Charger",
    "pc-lader": "Laptop charger",
    "PC-lader": "Laptop charger",
    "Pc-lader": "Laptop charger",
    # some extra common stuff if you ever use them:
    "mus": "Mouse",
    "Mus": "Mouse",
    "tastatur": "Keyboard",
    "Tastatur": "Keyboard",
    "skjerm": "Monitor",
    "Skjerm": "Monitor",
}


def translate_item(text: str) -> str:
    """
    Translate dynamic item names like 'lader' to English when lang=en.
    If we don't know the word, just return it as-is.
    """
    if not text:
        return text
    lang = session.get("lang", "no")
    if lang == "en":
        return item_translations_en.get(text, text)
    return text


# --------- DYNAMIC CLASS TRANSLATION (e.g. 'Ansatt' -> 'Employee') ---------

class_translations_en = {
    "Ansatt": "Employee",
    "ansatt": "Employee",
    "Lærer": "Teacher",
    "lærer": "Teacher",
}


def translate_class(text: str) -> str:
    """
    Translate dynamic class info like 'Ansatt' when lang=en.
    Real class names like '3IDA' will just pass through unchanged.
    """
    if not text:
        return text
    lang = session.get("lang", "no")
    if lang == "en":
        return class_translations_en.get(text, text)
    return text


# -------------------- MODELS --------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    loans = db.relationship('Loan', backref='user', lazy=True)

class Item(db.Model):
    __tablename__ = "item"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Total count you own
    stock_total = db.Column(db.Integer, nullable=False, default=0)
    # How many are currently available (not out on loan)
    stock_available = db.Column(db.Integer, nullable=False, default=0)

    def in_use(self):
        return max(0, self.stock_total - self.stock_available)



class PC(db.Model):
    __tablename__ = "pc"  # stabilt tabellnavn

    id = db.Column(db.Integer, primary_key=True)
    ok_number = db.Column(db.String(50), unique=True, nullable=False)
    model_type = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.String(200))

    def active_loan(self):
        return Loan.query.filter_by(pc_id=self.id, is_returned=False).first()

    def is_loaned_out(self):
        return self.active_loan() is not None


class Loan(db.Model):
    __tablename__ = "loan"

    id = db.Column(db.Integer, primary_key=True)
    borrower_name = db.Column(db.String(100), nullable=False)
    borrower_phone = db.Column(db.String(30))
    class_info = db.Column(db.String(50))
    item = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.String(200))
    checkout_date = db.Column(db.DateTime, default=datetime.utcnow)
    value = db.Column(db.String(100))
    due_date = db.Column(db.DateTime, nullable=True)
    return_date = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_returned = db.Column(db.Boolean, default=False)

    pc_id = db.Column(db.Integer, db.ForeignKey('pc.id'), nullable=True)
    pc = db.relationship('PC', backref='loans')

    # NEW: link to inventory item (charger, etc.)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    item_obj = db.relationship('Item')



# -------------------- HELPERS --------------------

def utc_to_local(utc_dt):
    """Konverterer UTC-datetime til Europe/Oslo. Faller tilbake til UTC hvis tzdata mangler."""
    if utc_dt is None:
        return None

    # If no tz DB, just return naive/UTC-ish time
    if OSLO_TZ is None:
        return utc_dt

    local_tz = OSLO_TZ
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=UTC_TZ)
    return utc_dt.astimezone(local_tz)


def local_today():
    """Return today's date in Europe/Oslo. Faller tilbake til lokal serverdato hvis tzdata mangler."""
    if OSLO_TZ is None:
        return datetime.now().date()
    return datetime.now(OSLO_TZ).date()


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Du må logge inn først.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Administrator-tilgang kreves.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrap


# Gjør is_admin, t, item_t, class_t og current_lang tilgjengelig i alle templates
@app.context_processor
def inject_admin_flag():
    return {
        "is_admin": session.get("is_admin", False),
        "t": translate,
        "item_t": translate_item,
        "class_t": translate_class,  # 👈 use this in templates for loan.class_info
        "current_lang": session.get("lang", "no"),
    }


def adjust_item_stock(item_id, delta: int):
    """
    Adjust `stock_available` on an Item.
    delta = -1 when loaning out
    delta = +1 when returning
    """
    if not item_id:
        return

    item = Item.query.get(item_id)
    if not item:
        return

    new_available = (item.stock_available or 0) + int(delta)
    # Never below 0, never above stock_total
    new_available = max(0, min(new_available, item.stock_total or 0))
    item.stock_available = new_available


# -------------------- DB INIT + SEED --------------------

with app.app_context():
    db.create_all()

    # Auto-opprett første admin hvis databasen er tom
    if User.query.count() == 0:
        default_admin = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            is_admin=True
        )
        db.session.add(default_admin)
        db.session.commit()
        print("✅ Opprettet standard admin: admin / admin123")


# -------------------- LANGUAGE ROUTE --------------------

@app.route('/lang/<lang_code>')
def set_language(lang_code):
    """Set language in session and redirect back."""
    if lang_code not in ("no", "en"):
        lang_code = "no"
    session["lang"] = lang_code

    next_url = request.referrer
    if not next_url:
        # Hvis ikke logget inn, gå til login. Ellers dashboard.
        if 'user_id' in session:
            next_url = url_for('dashboard')
        else:
            next_url = url_for('login')

    return redirect(next_url)


# -------------------- ROUTES: AUTH --------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Innlogging vellykket.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ugyldig brukernavn eller passord.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Du er nå logget ut.', 'info')
    return redirect(url_for('login'))


# -------------------- ROUTES: DASHBOARD & LOANS --------------------

@app.route('/dashboard')
@login_required
def dashboard():
    active_loans = Loan.query.filter_by(is_returned=False).all()
    returned_loans = Loan.query.filter_by(is_returned=True).all()

    today_local = local_today()

    for loan in active_loans + returned_loans:
        loan.checkout_date_local = utc_to_local(loan.checkout_date)
        loan.return_date_local = utc_to_local(loan.return_date)

        if loan.pc:
            loan.pc_label = f"{loan.pc.ok_number} – {loan.pc.model_type}"
            loan.pc_ok = loan.pc.ok_number
            loan.pc_model = loan.pc.model_type
        else:
            loan.pc_label = ""
            loan.pc_ok = ""
            loan.pc_model = ""

        loan.overdue = (
            not loan.is_returned
            and loan.due_date is not None
            and loan.due_date.date() < today_local
        )

    overdue_count = sum(1 for l in active_loans if l.overdue)
    returned_today_count = sum(
        1 for l in returned_loans
        if l.return_date_local and l.return_date_local.date() == today_local
    )

    total_active = len(active_loans)
    total_returned = len(returned_loans)

    # NEW: low stock items (<= 2 available, but > 0 total)
    low_stock_items = Item.query.filter(
        Item.stock_total > 0,
        Item.stock_available <= 2
    ).order_by(Item.name.asc()).all()

    return render_template(
        'dashboard.html',
        active_loans=active_loans,
        returned_loans=returned_loans,
        total_active=total_active,
        overdue_count=overdue_count,
        returned_today_count=returned_today_count,
        total_returned=total_returned,
        low_stock_items=low_stock_items  # NEW
    )


@app.route('/api/borrower/last')
@login_required
def api_borrower_last():
    """
    Return last loan data for a borrower name (exact match, case-insensitive).
    Used to auto-fill class, phone, etc. in 'New loan' form.
    """
    name = request.args.get('name', '').strip()
    if not name:
        return {"ok": False, "error": "missing_name"}, 400

    loan = (
        Loan.query
        .filter(func.lower(Loan.borrower_name) == func.lower(name))
        .order_by(Loan.checkout_date.desc())
        .first()
    )

    if not loan:
        return {"ok": False, "error": "not_found"}, 404

    return {
        "ok": True,
        "data": {
            "borrower_phone": loan.borrower_phone or "",
            "class_info": loan.class_info or "",
            "last_item": loan.item or "",
            "pc_id": loan.pc_id
        }
    }


@app.route('/loan/new', methods=['GET', 'POST'])
@login_required
def new_loan():
    pcs = PC.query.order_by(PC.ok_number.asc()).all()
    # NEW: load items (for dropdown)
    items = Item.query.order_by(Item.name.asc()).all()

    if request.method == 'POST':
        borrower_name = request.form.get('borrower_name', '').strip()
        borrower_phone = request.form.get('borrower_phone', '').strip()
        class_info = request.form.get('class_info', '').strip()
        item_text = request.form.get('item', '').strip()
        reason = request.form.get('reason', '').strip()
        value = request.form.get('value', '').strip()
        due_date_str = request.form.get('due_date')
        pc_id = request.form.get('pc_id')  # optional

        # NEW: selected inventory item (optional)
        item_id_str = request.form.get('item_id')
        selected_item_id = int(item_id_str) if item_id_str else None

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                flash('Ugyldig frist-dato. Bruk format ÅÅÅÅ-MM-DD.', 'danger')
                return redirect(url_for('new_loan'))

        if not borrower_name or not item_text:
            flash('Navn og utstyr er påkrevd.', 'danger')
            return redirect(url_for('new_loan'))

        # If an Item is selected and item_text is empty, use item name
        if selected_item_id and not item_text:
            selected_item = Item.query.get(selected_item_id)
            if selected_item:
                item_text = selected_item.name

        selected_pc_id = int(pc_id) if pc_id else None

        # Block new loan if PC already loaned out
        if selected_pc_id:
            already_out = Loan.query.filter_by(pc_id=selected_pc_id, is_returned=False).first()
            if already_out:
                flash("Denne PC-en er allerede utlånt.", "danger")
                return redirect(url_for('new_loan'))

        loan = Loan(
            borrower_name=borrower_name,
            borrower_phone=borrower_phone,
            class_info=class_info,
            item=item_text,
            reason=reason,
            value=value,
            due_date=due_date,
            pc_id=selected_pc_id,
            user_id=session['user_id'],
            item_id=selected_item_id  # NEW
        )

        # NEW: adjust inventory – only for active loan
        if selected_item_id:
            adjust_item_stock(selected_item_id, -1)

        db.session.add(loan)
        db.session.commit()

        flash('Utlån registrert.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('new_loan.html', pcs=pcs, items=items)



@app.route('/loan/<int:loan_id>')
@login_required
def loan_detail(loan_id):
    loan = Loan.query.get_or_404(loan_id)

    loan.checkout_date_local = utc_to_local(loan.checkout_date)
    loan.return_date_local = utc_to_local(loan.return_date)

    is_admin = session.get('is_admin', False)
    is_owner = loan.user_id == session.get('user_id')

    if not is_admin and not is_owner:
        flash('Du har ikke tilgang til å se dette utlånet.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template(
        'loan_detail.html',
        loan=loan,
        is_admin=is_admin,
        is_owner=is_owner
    )


@app.route('/loan/<int:loan_id>/return', methods=['POST'])
@login_required
def return_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)

    is_admin = session.get('is_admin', False)
    is_owner = loan.user_id == session.get('user_id')

    if not is_admin and not is_owner:
        flash('Du har ikke tilgang til å returnere dette utlånet.', 'danger')
        return redirect(url_for('dashboard'))

    if loan.is_returned:
        flash('Dette utlånet er allerede markert som returnert.', 'info')
        return redirect(url_for('loan_detail', loan_id=loan_id))

    loan.is_returned = True
    loan.return_date = datetime.utcnow()

    # NEW: item goes back in stock
    if loan.item_id:
        adjust_item_stock(loan.item_id, +1)

    db.session.commit()

    flash('Utlånet er markert som returnert.', 'success')
    return redirect(url_for('loan_detail', loan_id=loan_id))



@app.route('/loan/<int:loan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    pcs = PC.query.order_by(PC.ok_number.asc()).all()
    items = Item.query.order_by(Item.name.asc()).all()  # NEW

    is_admin = session.get('is_admin', False)
    is_owner = loan.user_id == session.get('user_id')

    if not is_admin and not is_owner:
        flash('Du har ikke tilgang til å endre dette utlånet.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        borrower_name = request.form.get('borrower_name', '').strip()
        borrower_phone = request.form.get('borrower_phone', '').strip()
        class_info = request.form.get('class_info', '').strip()
        item_text = request.form.get('item', '').strip()
        reason = request.form.get('reason', '').strip()
        value = request.form.get('value', '').strip()
        due_date_str = request.form.get('due_date')
        pc_id = request.form.get('pc_id')

        # NEW: item from inventory
        item_id_str = request.form.get('item_id')
        new_item_id = int(item_id_str) if item_id_str else None
        old_item_id = loan.item_id

        if not borrower_name or not item_text:
            flash('Navn og utstyr er påkrevd.', 'danger')
            return redirect(url_for('edit_loan', loan_id=loan.id))

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                flash('Ugyldig frist-dato. Bruk format ÅÅÅÅ-MM-DD.', 'danger')
                return redirect(url_for('edit_loan', loan_id=loan.id))

        selected_pc_id = int(pc_id) if pc_id else None

        if selected_pc_id and selected_pc_id != loan.pc_id:
            already_out = Loan.query.filter_by(pc_id=selected_pc_id, is_returned=False).first()
            if already_out:
                flash("Denne PC-en er allerede utlånt.", "danger")
                return redirect(url_for('edit_loan', loan_id=loan.id))

        # If using inventory item and no text given, use item name
        if new_item_id and not item_text:
            selected_item = Item.query.get(new_item_id)
            if selected_item:
                item_text = selected_item.name

        # Update loan fields
        loan.borrower_name = borrower_name
        loan.borrower_phone = borrower_phone
        loan.class_info = class_info
        loan.item = item_text
        loan.reason = reason
        loan.value = value
        loan.due_date = due_date
        loan.pc_id = selected_pc_id

        # NEW: adjust stock if inventory item changed
        if not loan.is_returned:
            if old_item_id != new_item_id:
                # Old item becomes available again
                if old_item_id:
                    adjust_item_stock(old_item_id, +1)
                # New item is now loaned out
                if new_item_id:
                    adjust_item_stock(new_item_id, -1)

        loan.item_id = new_item_id

        db.session.commit()
        flash("Utlån oppdatert.", "success")
        return redirect(url_for('loan_detail', loan_id=loan.id))

    return render_template(
        'loan_edit.html',
        loan=loan,
        pcs=pcs,
        items=items,
        is_admin=is_admin,
        is_owner=is_owner
    )

@app.route('/loan/<int:loan_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)

    # NEW: if loan is still active and has item, put it back in stock
    if not loan.is_returned and loan.item_id:
        adjust_item_stock(loan.item_id, +1)

    db.session.delete(loan)
    db.session.commit()

    flash('Utlånet ble slettet.', 'success')
    return redirect(url_for('dashboard'))



# -------------------- PC INVENTORY --------------------

@app.route('/pcs')
@login_required
def pc_inventory():
    pcs = PC.query.order_by(PC.ok_number.asc()).all()
    return render_template('pc_inventory.html', pcs=pcs)


# ADD PC ROUTE — endpoint name must be "add_pc"
@app.route('/pcs/add', methods=['GET', 'POST'], endpoint="add_pc")
@login_required
@admin_required
def add_pc():
    if request.method == 'POST':
        ok_number = request.form.get('ok_number', '').strip()
        model_type = request.form.get('model_type', '').strip()
        notes = request.form.get('notes', '').strip()

        if not ok_number or not model_type:
            flash("OK-nummer og modelltype er påkrevd.", "danger")
            return redirect(url_for('add_pc'))

        existing = PC.query.filter_by(ok_number=ok_number).first()
        if existing:
            flash("Denne PC-en finnes allerede.", "danger")
            return redirect(url_for('add_pc'))

        pc = PC(ok_number=ok_number, model_type=model_type, notes=notes or None)
        db.session.add(pc)
        db.session.commit()

        flash("PC lagt til i oversikten.", "success")
        return redirect(url_for('pc_inventory'))

    return render_template('add_pc.html')


@app.route('/pcs/<int:pc_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_pc(pc_id):
    pc = PC.query.get_or_404(pc_id)

    if request.method == 'POST':
        ok_number = request.form.get('ok_number', '').strip()
        model_type = request.form.get('model_type', '').strip()
        notes = request.form.get('notes', '').strip()

        if not ok_number or not model_type:
            flash("OK-nummer og modelltype er påkrevd.", "danger")
            return redirect(url_for('edit_pc', pc_id=pc.id))

        # prevent OK-number collision with another PC
        existing = PC.query.filter(PC.ok_number == ok_number, PC.id != pc.id).first()
        if existing:
            flash("Denne PC-en finnes allerede.", "danger")
            return redirect(url_for('edit_pc', pc_id=pc.id))

        pc.ok_number = ok_number
        pc.model_type = model_type
        pc.notes = notes

        db.session.commit()
        flash("PC oppdatert.", "success")
        return redirect(url_for('pc_inventory'))

    return render_template('edit_pc.html', pc=pc)


@app.route('/pcs/<int:pc_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_pc(pc_id):
    pc = PC.query.get_or_404(pc_id)

    try:
        db.session.delete(pc)
        db.session.commit()
        flash("PC slettet fra lager.", "success")
    except Exception:
        db.session.rollback()
        flash("Noe gikk galt ved sletting av PC.", "danger")

    return redirect(url_for('pc_inventory'))


# -------------------- ADMIN USERS --------------------

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.order_by(User.id.asc()).all()
    return render_template('admin_panel.html', users=users)


@app.route('/admin/user/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        is_admin_flag = request.form.get('is_admin') == 'on'

        if not username or not password:
            flash('Brukernavn og passord er påkrevd.', 'danger')
            return redirect(url_for('add_user'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Brukernavnet er allerede i bruk.', 'danger')
            return redirect(url_for('add_user'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password, is_admin=is_admin_flag)

        db.session.add(new_user)
        db.session.commit()

        flash('Bruker lagt til.', 'success')
        return redirect(url_for('admin_panel'))

    return render_template('add_user.html')


@app.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == session.get('user_id'):
        flash("Du kan ikke fjerne admin-rettigheter fra din egen bruker.", "danger")
        return redirect(url_for('admin_panel'))

    user.is_admin = not user.is_admin
    db.session.commit()

    status = "nå administrator" if user.is_admin else "ikke lenger administrator"
    flash(f"{user.username} er {status}.", "success")
    return redirect(url_for('admin_panel'))


@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == session.get('user_id'):
        flash("Du kan ikke slette din egen bruker.", "danger")
        return redirect(url_for('admin_panel'))

    if user.loans and len(user.loans) > 0:
        flash("Kan ikke slette bruker som har registrerte utlån.", "danger")
        return redirect(url_for('admin_panel'))

    db.session.delete(user)
    db.session.commit()

    flash(f"Bruker {user.username} ble slettet.", "success")
    return redirect(url_for('admin_panel'))


# -------------------- PROFILE --------------------

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not check_password_hash(user.password_hash, current_password):
            flash("Nåværende passord er feil.", "danger")
            return redirect(url_for('profile'))

        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                flash("Brukernavnet er allerede i bruk.", "danger")
                return redirect(url_for('profile'))
            user.username = new_username
            session['username'] = new_username

        if new_password:
            if new_password != confirm_password:
                flash("Nytt passord og bekreftelse matcher ikke.", "danger")
                return redirect(url_for('profile'))
            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash("Profil oppdatert.", "success")
        return redirect(url_for('profile'))

    return render_template('user_profile.html', user=user)


# -------------------- MAIN --------------------

if __name__ == '__main__':
    app.run(
        debug=True,
        port=5000,
        host='0.0.0.0',
        threaded=True,
        use_reloader=True,
        use_debugger=True
    )
