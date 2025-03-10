from flask import Flask, render_template, request, url_for, redirect, flash


from src.repositories.Post_Repository import post_repository_singleton
from src.repositories.User_Repository import user_repository_singleton
from src.repositories.Comment_Repository import comment_repository_singleton
from src.models.models import Post

from src.models.models import db

app = Flask(__name__) # __name__ refers to the module name
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:henry123@localhost:5432/posty_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


global post_list
post_list = post_repository_singleton.get_all_posts()

#login stuff
global logged_in 
logged_in = False
global current_user
current_user = None


@app.route('/') # Python decorator, new syntax
def index():
    post_list = post_repository_singleton.get_all_posts()
    return render_template("index.html", current_user = current_user, post_list= post_list)

@app.route('/login_page') # Python decorator, new syntax
def login_page():
    return render_template("login_page.html", current_user = current_user)

@app.route('/home_page') # Python decorator, new syntax
def home_page():
    return render_template("index.html", current_user = current_user, post_list= post_list)

@app.route('/sign_up_page') # Python decorator, new syntax
def sign_up_page():
    return render_template("sign_up_page.html", current_user = current_user)

@app.route('/account_info_page') # Python decorator, new syntax
def account_info_page():
    return render_template("account_info.html", current_user = current_user)


@app.route('/create_new_post_page') # Python decorator, new syntax
def create_new_post_page():

    if(current_user == None):
        #need to be logged in to make posts
        return redirect("/")

    return render_template("create_new_post.html", current_user = current_user)


@app.post('/create_new_user')  # Python decorator, new syntax
def create_new_user():

    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    username = request.form.get('username')
    user_university = request.form.get('university')
    user_email = request.form.get('email')
    user_password = request.form.get('password')
    user_repeat_password = request.form.get('repeat_password')

    if (user_password != user_repeat_password):
        # TODO: handle this
        flash('Password Does Not Match')
        return redirect("/sign_up_page")

    user_repository_singleton.create_user(
        firstname, lastname, username, user_email, user_password, user_university)

    flash('Form Submitted Successfully')

    return redirect("/login_page")



@app.post('/login_page/login') # Python decorator, new syntax
def login():
    global logged_in
    global current_user


    username = request.form.get('username')
    user_password = request.form.get('password')


    user = user_repository_singleton.get_user_by_username(username)

    if(user == None):
        #user doesn't exist
        print("user  === none")
        return redirect("/login_page")

    if(user.user_password != user_password):
        #passwords don't match
        print("passwrods don't match")
        return redirect("/login_page")

    print(logged_in)
    if current_user == None:
        print("No current user")
    else:
        print(current_user.name)

    #at this point user exists and password matches
    logged_in = True
    current_user = user

    print(logged_in)
    print(current_user.username)

    #go back to index, name and uni will appear at top of screen
    return redirect("/")




@app.post('/create_new_post') # Python decorator, new syntax
def create_new_post():
    global post_list

    title = request.form.get('title')
    post_text = request.form.get('post')

    if(current_user != None):

        post_repository_singleton.create_post(current_user.university, title, post_text, current_user.user_id)
        #update post list
        post_list = post_repository_singleton.get_all_posts()



    return redirect("/")



@app.post('/account_info/logout') # Python decorator, new syntax
def logout():
    global current_user

    current_user = None

    return redirect("/")


@app.route('/post_viewer/<int:post_id>')
def post_viewer(post_id):
    global post_list

    selected_post_id = post_id

    #grabbing posts using post ids
    user_post = None
    
    for post in post_list:
        if(str(selected_post_id ) == str(post.post_id)):
            user_post = post


    if(user_post == None):
        return redirect("/")



    #need to find list of all comments associated with this particular post and pass that into render tempate
    comments = post_repository_singleton.returnAllComments(selected_post_id )
    print(comments)


    #if the comments list is empty display the page
    if(len(comments) == 0):
        return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = {})



    #organize comments list into a dictionary where
    # {  parents comment: [child comment 1, child comment 2, child comment 3]   }

    comment_dictionary = generate_comment_dictionary(post_id)

    print(comment_dictionary)

    return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = comment_dictionary, parent_comment= False)


@app.route('/comment_text_area/<int:post_id>')
def post_viewer_comment_text_area(post_id):

    #get post object using id
    user_post = post_repository_singleton.get_post_by_id(post_id)

    #get comment dictionary
    comment_dictionary = generate_comment_dictionary(post_id)

    #can't comment if not logged in
    if(not logged_in):
        #if the comments list is empty display the page
        if(len(comment_dictionary) == 0):
            return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = {}, parent_comment=False)

        return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = comment_dictionary, parent_comment= False)

    #if the comments list is empty display the page
    if(len(comment_dictionary) == 0):
        return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = {}, parent_comment=True)

    return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = comment_dictionary, parent_comment= True)
    

@app.route('/comment_text_area/comment/<int:post_id>')
def post_viewer_comment(post_id):

    comment_dictionary = generate_comment_dictionary(post_id)
    user_post = post_repository_singleton.get_post_by_id(post_id)

    #can't comment if not logged in
    if(not logged_in):
        #if the comments list is empty display the page
        if(len(comment_dictionary) == 0):
            return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = {}, parent_comment=False)

        return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = comment_dictionary, parent_comment= False)


    comment_text = request.args.get('comment_text')

    comment_repository_singleton.create_parent_comment(comment_text, post_id , current_user.user_id)
    comment_dictionary = generate_comment_dictionary(post_id)

    #if the comments list is empty display the page
    if(len(comment_dictionary) == 0):
        return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = {}, parent_comment=False)

    return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = comment_dictionary, parent_comment= False)
    


@app.route('/comment_text_area/<int:post_id>/<int:comment_id>')
def post_viewer_reply_to_comment():
    pass
    #return render_template("post_viewer.html", current_user = current_user, post = user_post, comment_dictionary = comment_dictionary)


def generate_comment_dictionary(selected_post_id):
    #organize comments list into a dictionary where
    # {  parents comment: [child comment 1, child comment 2, child comment 3]   }

    comments = post_repository_singleton.returnAllComments(selected_post_id )

    comment_dictionary = {}

    #parent comments
    for comment in comments:
        if comment.parent_comment_id == None:
            comment_dictionary[comment] = []

    #child comments
    for comment in comment_dictionary:
        if comment.parent_comment_id != None:
            comment_dictionary[comment_repository_singleton.get_comment_by_id(comment.parent_comment_id)] = comment

    return comment_dictionary