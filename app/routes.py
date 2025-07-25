from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from app.extensions import db, login_manager
from app.forms import OrderForm, RegistrationForm, LoginForm, ProfileForm, SettingForm, ApplicationForm
from app.models import (
    BlogPost, Sample, User, Testimonial, Lead, Writer, SiteReview, ChatMessage, Message,
    Announcement, Order, OrderFile, Application
)
from flask_mail import Message as MailMessage
from app import mail

main = Blueprint("main", __name__)

@main.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "public")
    writers = Application.query.filter_by(approved=True).all()

    announcements = Announcement.query.filter_by(audience=category)\
        .order_by(Announcement.created_at.desc())\
        .paginate(page=page, per_page=5)

    writers = Writer.query.order_by(Writer.created_at.desc()).limit(4).all()
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(3).all()
 
    return render_template(
        "index.html",
        announcements=announcements,
        selected_category=category,
        writers=writers,
        posts=posts
    )

@main.route('/lead', methods=['POST'])
def lead():
    topic = request.form.get('topic')
    new_lead = Lead(topic=topic)
    db.session.add(new_lead)
    db.session.commit()
    return redirect(url_for('main.index'))

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_grouped_chats():
    chats = Message.query.order_by(Message.timestamp.asc()).all()
    grouped = {}
    for msg in chats:
        grouped.setdefault(msg.sender_id, []).append(msg)
    return grouped

@main.route('/Register now', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(email=form.email.data, name=form.name.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    content = data.get('message')
    if not content:
        return jsonify({'error': 'Empty message'}), 400

    msg = Message(sender_id=current_user.id, receiver_id=0, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'status': 'Message sent'})

@main.route('/get_messages', methods=['GET'])
@login_required
def get_messages():
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | 
        (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp).all()
    return jsonify([
        {
            'content': m.content,
            'is_admin': m.is_admin,
            'timestamp': m.timestamp.strftime("%Y-%m-%d %H:%M") if m.timestamp else None
        } for m in messages
    ])

@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("main.index"))
        else:
            flash("Invalid email or password", "danger")
    return render_template("login.html", form=form)

@main.route("/protected")
@login_required
def protected():
    return "You must be logged in to view this page."

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("main.login"))

login_manager.login_view = 'main.login'
@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("You must log in or sign up to access this page.", "warning")
    return redirect(url_for('main.login'))

@main.route('/admin/messages')
def admin_messages():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin_messages.html')

@main.route('/writers')
def public_writers():
    writers = Writer.query.filter_by(approved=True).order_by(Writer.id.desc()).all()
    return render_template('public_writers.html', writers=writers)

@main.route("/Blog")
def blog_list():
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)

    blogs = BlogPost.query
    if query:
        blogs = blogs.filter(BlogPost.title.contains(query))

    blogs = blogs.order_by(BlogPost.created_at.desc()).paginate(page=page, per_page=5)
    return render_template("Blog.html", blogs=blogs, query=query)

@main.route('/admin')
def admin_dashboard():
    stats = {
        "messages": Message.query.count(),
        "testimonials": Testimonial.query.count(),
        "writers": Writer.query.count(),
        "leads": Lead.query.count(),
    }

    grouped_chats = get_grouped_chats()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        grouped_chats=grouped_chats,
        announcements=announcements
    )
    
@main.route('/admin/leads')
def admin_leads():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template("admin_leads.html", leads=leads)

@main.route('/admin/testimonials', methods=['GET', 'POST'])
def admin_testimonials():
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        rating = int(request.form['rating'])
        testimonial = Testimonial(name=name, content=content, rating=rating)
        db.session.add(testimonial)
        db.session.commit()
        return redirect(url_for('main.admin_testimonials'))

    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin_testimonials.html', testimonials=testimonials)

@main.route('/admin/testimonial/<int:id>/edit', methods=['GET', 'POST'])
def edit_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    if request.method == 'POST':
        testimonial.name = request.form['name']
        testimonial.content = request.form['content']
        testimonial.rating = int(request.form['rating'])
        db.session.commit()
        return redirect(url_for('main.admin_testimonials'))
    return render_template('edit_testimonial.html', testimonial=testimonial)

@main.route('/admin/testimonial/<int:id>/delete')
def delete_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    return redirect(url_for('main.admin_testimonials'))

@main.route("/admin/samples", methods=["GET", "POST"])
def admin_samples():
    if request.method == "POST":
        title = request.form["title"]
        category = request.form["category"]
        content = request.form["content"]
        new_sample = Sample(title=title, category=category, content=content)
        db.session.add(new_sample)
        db.session.commit()
        return redirect(url_for("main.admin_samples"))

    samples = Sample.query.order_by(Sample.created_at.desc()).all()
    return render_template("admin_samples.html", samples=samples)

@main.route('/admin/samples/<int:id>/delete')
def delete_samples(id):
    post = Sample.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Sample post deleted.', 'info')
    return redirect(url_for('main.admin_samples'))

@main.route('/admin/reviews', methods=['GET', 'POST'])
def admin_reviews():
    if request.method == 'POST':
        reviewer = request.form['reviewer']
        comment = request.form['comment']
        stars = int(request.form['stars'])

        new_review = SiteReview(reviewer=reviewer, comment=comment, stars=stars)
        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for('main.admin_reviews'))

    reviews = SiteReview.query.order_by(SiteReview.created_at.desc()).all()
    return render_template("admin_reviews.html", reviews=reviews)

@main.route('/admin/reviews/<int:id>/delete')
def delete_review(id):
    review = SiteReview.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    return redirect(url_for('main.admin_reviews'))

@main.route('/admin/writers')
def admin_writers():
    writers = Writer.query.order_by(Writer.created_at.desc()).all()
    return render_template('admin_writers.html', writers=writers)

@main.route('/admin/writer/<int:id>/approve')
def approve_writer(id):
    writer = Writer.query.get_or_404(id)
    writer.approved = True
    db.session.commit()
    flash('Writer approved!', 'success')
    return redirect(url_for('main.admin_writers'))

@main.route('/admin/writer/<int:id>/delete')
def delete_writer(id):
    writer = Writer.query.get_or_404(id)
    db.session.delete(writer)
    db.session.commit()
    flash('Writer deleted.', 'info')
    return redirect(url_for('main.admin_writers'))

@main.route('/writer/thanks')
def writer_thank_you():
    return render_template('writer_thank_you.html')

@main.route('/admin/writer/add', methods=['GET', 'POST'])
@login_required
def add_writer():
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form['subject']
        image_url = request.form.get('image_url')
        approved = True  # Admin-added writers are auto-approved
        new_writer = Writer(name=name, subject=subject, image_url=image_url, approved=approved)
        db.session.add(new_writer)
        db.session.commit()
        flash("Writer added successfully.", "success")
        return redirect(url_for('main.admin_writers'))
    return render_template('admin_writer_add.html')

@main.route("/order", methods=["GET", "POST"])
@login_required
def order():
    form = OrderForm()
    if form.validate_on_submit():
        order = Order(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            details=form.details.data,
            deadline=form.deadline.data
        )
        db.session.add(order)
        db.session.commit()

        # Send email
        msg = MailMessage(
            subject="✅ We Received Your Order",
            recipients=[form.email.data],
            body=f"""
Hi {form.name.data},

Thanks for your order!

📌 Subject: {form.subject.data}
📅 Deadline: {form.deadline.data.strftime('%Y-%m-%d')}
📝 Details: {form.details.data}

We’ll get back to you shortly.

Regards,
Your Website Team
""",
        )
        mail.send(msg)

        flash("Order submitted successfully! A confirmation email has been sent.", "success")
        return redirect(url_for("main.order_confirmation"))

    return render_template("order.html", form=form)

@main.route("/order/confirmation")
def order_confirmation():
    return render_template("order_confirmation.html")

@main.route("/admin/orders")
def admin_orders():
    q = request.args.get("q")
    if q:
        orders = Order.query.filter(
            (Order.name.ilike(f"%{q}%")) | (Order.subject.ilike(f"%{q}%"))
        ).order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin_orders.html", orders=orders)

@main.route('/admin/order/<int:id>/update', methods=['GET', 'POST'])
def update_order(id):
    order = Order.query.get_or_404(id)
    if request.method == 'POST':
        order.status = request.form['status']
        db.session.commit()
        return redirect(url_for('main.admin_orders'))
    return render_template('admin_orders.html', order=order)

@main.route("/admin/order/delete/<int:id>")
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash("Order deleted successfully.", "info")
    return redirect(url_for("main.admin_orders"))

@main.route('/contact', methods=['POST'])
def contact():
    message = request.form.get('message')
    name = request.form.get('name')
    email = request.form.get('email')
    # Choose how to associate sender/receiver. Here, sender_id=0 (guest), receiver_id=1 (admin)
    new_msg = Message(
        sender_id=0,
        receiver_id=1,
        content=message,
        is_admin=False
    )
    db.session.add(new_msg)
    db.session.commit()
    return redirect(url_for('main.index', success=True))

@main.route('/admin/chat/grouped')
def admin_chat_grouped():
    grouped_chats = get_grouped_chats()
    return render_template('admin_chat_grouped.html', grouped_chats=grouped_chats)

@main.route('/admin/chat/reply', methods=['POST'])
def reply_to_user():
    user_id = request.form.get('user_id')
    message = request.form.get('message')

    msg = Message(
        sender_id=current_user.id,    # admin's user id
        receiver_id=int(user_id),     # the user being replied to
        content=message,
        is_admin=True
    )
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for('main.admin_chat_grouped'))

@main.route('/chat/messages')
def get_messages_json():
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    result = [{
        "sender_id": msg.sender_id,
        "receiver_id": msg.receiver_id,
        "content": msg.content,
        "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M") if msg.timestamp else None
    } for msg in messages]
    return jsonify(result)

@main.route('/admin_chat')
def admin_chat():
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    return render_template("admin_chat.html")

@main.route('/admin/uploads', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded = request.files['file']
        if uploaded and allowed_file(uploaded.filename):
            filename = secure_filename(uploaded.filename)
            uploaded.save(os.path.join(UPLOAD_FOLDER, filename))

            file_entry = OrderFile(filename=filename, uploader='admin')
            db.session.add(file_entry)
            db.session.commit()
            return redirect(url_for('main.upload_file'))

    files = OrderFile.query.order_by(OrderFile.uploaded_at.desc()).all()
    return render_template('admin_uploads.html', files=files)

@main.route('/admin/payments')
def admin_payments():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin_payments.html')

@main.route("/Samples")
def Samples():
    samples = Sample.query.order_by(Sample.created_at.desc()).all()
    return render_template("Samples.html", samples=samples)

@main.route('/admin/announcements', methods=['GET', 'POST'])
def admin_announcements():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        audience = request.form.get('audience', 'public')
        category = request.form.get('category', 'general')
        new_announcement = Announcement(title=title, body=body, audience=audience, category=category)
        db.session.add(new_announcement)
        db.session.commit()
        flash("Announcement posted!", "success")
        return redirect(url_for('main.admin_announcements'))

    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')

    query = Announcement.query.order_by(Announcement.created_at.desc())
    if category:
        query = query.filter_by(category=category)

    pagination = query.paginate(page=page, per_page=5)
    announcements = pagination.items

    return render_template("admin_announcements.html",
                           announcements=announcements,
                           pagination=pagination,
                           selected_category=category)

@main.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin_settings.html')

@main.route('/Blog')
def public_blogs():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog.html', blogs=posts)

@main.route("/Blog/<int:id>")
def blog_detail(id):
    blog = BlogPost.query.get_or_404(id)
    return render_template("blog_detail.html", blog=blog)

@main.route('/admin/Blog', methods=['GET', 'POST'])
def admin_Blog():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            return "Missing data", 400

        new_post = BlogPost(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('main.admin_Blog'))

    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin_Blog.html', posts=posts)

@main.route('/admin/blog/<int:id>/edit', methods=['GET', 'POST'])
def edit_blog(id):
    post = BlogPost.query.get_or_404(id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Blog post updated!', 'success')
        return redirect(url_for('main.admin_Blog'))
    return render_template('edit_blog.html', post=post)

@main.route('/admin/blog/<int:id>/delete')
def delete_blog(id):
    post = BlogPost.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted.', 'info')
    return redirect(url_for('main.admin_Blog'))

@main.route('/admin/messages', methods=['GET'])
@login_required
def admin_view_all():
    if not current_user.is_admin:
        return "Forbidden", 403
    all_msgs = Message.query.order_by(Message.timestamp).all()
    return jsonify([
        {
            'from': m.sender_id,
            'to': m.receiver_id,
            'content': m.content,
            'is_admin': m.is_admin,
            'timestamp': m.timestamp.strftime("%Y-%m-%d %H:%M") if m.timestamp else None
        } for m in all_msgs
    ])

# ------------------------
# 🏢 Company Section Routes
# ------------------------
@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')

@main.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@main.route('/faq')
def faq():
    return render_template('faq.html')

@main.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

@main.route('/hiring')
def hiring():
    return render_template('hiring.html')

@main.route('/terms')
def terms():
    return render_template('terms.html')

@main.route('/fair-use')
def fair_use():
    return render_template('fair_use.html')

@main.route('/payment-policy')
def payment_policy():
    return render_template('payment_policy.html')

@main.route('/dont_buy_accounts')
def dont_buy_accounts():
    return render_template('dont_buy_accounts.html')

# ------------------------
# 🧾 Services Section Routes
# ------------------------

@main.route('/services/essay-writing')
def essay_writing():
    return render_template('services/essay_writing.html')

@main.route('/services/research-papers')
def research_papers():
    return render_template('services/research_papers.html')

@main.route('/services/case-studies')
def case_studies():
    return render_template('services/case_studies.html')

@main.route('/services/dissertations')
def dissertations():
    return render_template('services/dissertations.html')

@main.route('/services/theses')
def theses():
    return render_template('services/theses.html')

@main.route('/services/speeches')
def speeches():
    return render_template('services/speeches.html')

@main.route('/services/assignments')
def assignments():
    return render_template('services/assignments.html')

@main.route('/services/narrative-essays')
def narrative_essays():
    return render_template('services/narrative_essays.html')

@main.route('/services/analytical-essays')
def analytical_essays():
    return render_template('services/analytical_essays.html')

@main.route('/services/persuasive-essays')
def persuasive_essays():
    return render_template('services/persuasive_essays.html')

@main.route('/services/admission-help')
def admission_help():
    return render_template('services/admission_help.html')

@main.route('/services/literature-reviews')
def literature_reviews():
    return render_template('services/literature_reviews.html')

@main.route('/services/book-reports')
def book_reports():
    return render_template('services/book_reports.html')

@main.context_processor
def inject_now():
    from datetime import datetime
    return {'current_year': datetime.now().year}

@main.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash("✅ Profile updated successfully!", "success")
        return redirect(url_for("main.profile"))
    return render_template("profile.html", form=form)

@main.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = SettingForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash("✅ Changes made successfully!", "success")
        return redirect(url_for("main.settings"))
    return render_template("settings.html", form=form)

@main.route('/writer/apply', methods=['GET', 'POST'])
def writer_apply():
    form = ApplicationForm()
    if form.validate_on_submit():
        application = Application(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            bio=form.bio.data
        )
        db.session.add(application)
        db.session.commit()
        flash("Your application has been submitted! We'll review and notify you.", "success")
        return redirect(url_for('main.index'))
    return render_template('writer_apply.html', form=form)

@main.route("/my-orders")
@login_required
def my_orders():
    orders = current_user.orders
    return render_template("my_orders.html", orders=orders)