from flask import render_template, redirect, url_for, request, abort, current_app, flash
from flask_login import login_user, current_user, logout_user, login_required
from twittor.email import send_email
from twittor.forms import LoginForm, PasswordResetForm, RegisterFrom, EditProfileForm, TweetForm, DeleteTweetForm
from twittor.models import User, Tweet
from twittor import db

@login_required
def index():
    form = TweetForm()
    if form.validate_on_submit():
        if form.btn_cancel.data:
            return redirect(url_for('index', username = current_user.username))
        t = Tweet(body=form.tweet.data, author=current_user)
        db.session.add(t)
        db.session.commit()
        return redirect(url_for('index'))
    
    page_num = int(request.args.get('page') or 1)
    tweets = current_user.own_and_followed_tweets().paginate(page=page_num, per_page=current_app.config['TWEET_PER_PAGE'], error_out=False)

    delete_tweet_form = DeleteTweetForm()
    if delete_tweet_form.validate_on_submit():
        db.session.delete(current_user.tweets.id)
        db.session.commit()
        return redirect(url_for('index'))

    next_url = url_for('index', page=tweets.next_num) if tweets.has_next else None
    prev_url = url_for('index', page=tweets.prev_num) if tweets.has_prev else None
    return render_template(
        'index.html', tweets=tweets.items, form=form, next_url=next_url, prev_url=prev_url
        , delete_tweet_form=delete_tweet_form
    )

def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm(meta={'csrf': False})
    if form.validate_on_submit():
        u = User.query.filter_by(username=form.username.data).first()
        if u is None or not u.check_password(form.password.data):
            print('invalid username or password')
            return redirect(url_for('login'))
        login_user(u, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('index'))
    return render_template('login.html', title="Sign In", form=form)

def logout():
    logout_user()
    return redirect(url_for('login'))

def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterFrom()
    if form.validate_on_submit():
        user = User(username=form.username.data, email = form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', title='Registration', form=form)


@login_required
def user(username):
    u = User.query.filter_by(username=username).first()
    if u is None:
        abort(404)
    
    page_num = int(request.args.get('page') or 1)
    tweets = u.tweets.order_by(Tweet.create_time.desc()).paginate(
        page=page_num,
        per_page=current_app.config['TWEET_PER_PAGE'],
        error_out=False)

    delete_tweet_form = DeleteTweetForm()
    if delete_tweet_form.validate_on_submit():
        db.session.delete(tweets.items.id)
        db.session.commit()
        return redirect(url_for('profile', username = current_user.username))

    next_url = url_for(
        'profile',
        username=username,
        page=tweets.next_num) if tweets.has_next else None
    prev_url = url_for(
        'profile',
        username=username,
        page=tweets.prev_num) if tweets.has_prev else None
    
    if request.method == 'POST':
        if request.form['request_button'] == 'Follow':
            current_user.follow(u)
            db.session.commit()
        if request.form['request_button'] == 'Unfollow':
            current_user.unfollow(u)
            db.session.commit()
    return render_template(
        'user.html', title='Profile', tweets=tweets.items, user=u, next_url=next_url, prev_url=prev_url
        , delete_tweet_form=delete_tweet_form
    )

def page_not_found(e):
    return render_template('404.html'), 404

@login_required
def edit_profile():
    form = EditProfileForm()
    if request.method == 'GET':
        form.about_me.data = current_user.about_me
    if form.validate_on_submit():
        if form.btn_cancel.data:
            return redirect(url_for('profile', username = current_user.username))
        current_user.about_me = form.about_me.data
        db.session.commit()
        return redirect(url_for('profile', username = current_user.username))
    return render_template('edit_profile.html', title='Profile Editer', form=form)

def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash(
                "You should soon receive an email allowing you to reset your \
                password. Please make sure to check your spam and trash \
                if you can't find the eamil."
            )
            token = user.get_jwt()
            url = 'http://127.0.0.1:5000/password_reset/{}'.format(token)
            send_email(
                subject='subject',
                recipients=[user.email],
                text_body=url,
                html_body='<h1>{}</h1>'.format(url)
            )
        else:
            raise
        return redirect(url_for('login'))
    return render_template('password_reset_request.html', form=form)