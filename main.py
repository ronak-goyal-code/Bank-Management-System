from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import secrets
from datetime import datetime, timedelta

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="bankdb"
)
mycursor = mydb.cursor()

app = Flask(__name__)
secret_key = secrets.token_hex(16)
app.secret_key = secret_key

@app.route('/')
def home():
    if 'login_cust_id' in session:
        customer_id = session['login_cust_id']
        # Fetch account info
        mycursor.execute("SELECT * FROM Account WHERE customer_id = %s", (customer_id,))
        accounts = mycursor.fetchall()

        # Fetch active loan details if any
        mycursor.execute("SELECT * FROM Loan WHERE customer_id = %s AND status = 'active'", (customer_id,))
        active_loans = mycursor.fetchall()

        return render_template('home.html', accounts=accounts, active_loans=active_loans)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cust_id = request.form['customer_id']
        cust_password = request.form['password']
        
        sql = "SELECT customer_password FROM Customer WHERE customer_id = %s"
        mycursor.execute(sql, (cust_id,))
        password = mycursor.fetchone()
        
        if password and password[0] == cust_password:
            session['login_cust_id'] = cust_id
            return redirect(url_for('home'))
        
        error = 'Invalid customer_id or password. Please try again.'
        return render_template('login.html', title='Login', error=error)
    else:
        return render_template('login.html', title='Login')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('login_cust_id', None)
    return redirect(url_for('login'))

def insert_account_data(data, customer_id):
    try:
        # Insert data into Customer table
        add_customer = ("INSERT INTO Customer "
                        "(customer_id, customer_password, customer_name, email, phone_number, address, date_of_birth) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        customer_data = (customer_id, data['password'], data['name'], data['email'], data['phone'], data['address'], data['dob'])
        mycursor.execute(add_customer, customer_data)
        
        # Get the branch ID based on the selected branch name
        get_branch_id = ("SELECT branch_id FROM Branch WHERE branch_name = %s")
        mycursor.execute(get_branch_id, (data['branch'],))
        branch_id = mycursor.fetchone()[0]
        
        # Insert data into Account table
        add_account = ("INSERT INTO Account "
                       "(customer_id, branch_id, account_type, balance, status) "
                       "VALUES (%s, %s, %s, %s, %s)")
        account_data = (customer_id, branch_id, data['type'], 0.0, 'active')
        mycursor.execute(add_account, account_data)
        
        mydb.commit()
        
        return True
    except mysql.connector.Error as err:
        print("Error:", err)
        return False

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        mycursor.execute("SELECT customer_id FROM Customer ORDER BY customer_id DESC LIMIT 1")
        last_customer = mycursor.fetchone()
        if last_customer:
            last_customer_id = last_customer[0]
        else:
            last_customer_id = 0
        new_customer_id = last_customer_id + 1
        
        # Extract form data
        account_data = {
            'name': request.form['name'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'address': request.form['address'],
            'dob': request.form['dob'],
            'password': request.form['password'],
            'branch': request.form['branch'],
            'type': request.form['account_type']
        }
        
        # Insert account data into the database
        if insert_account_data(account_data, new_customer_id):
            mycursor.execute("SELECT account_number FROM Account WHERE customer_id = %s", (new_customer_id,))
            account_number = mycursor.fetchone()[0]

            # Redirect to the registration confirmation page with customer_id and account_id
            return render_template('registration_confirmation.html', customer_id=new_customer_id, account_number=account_number)
        else:
            return "Error occurred while opening the account. Please try again later."
    else:
        return render_template('register.html')

def get_account_info(customer_id):
    try:
        mycursor.execute("SELECT account_number FROM Account WHERE customer_id = %s", (customer_id,))
        account_number = mycursor.fetchone()
        return account_number[0] if account_number else None
    except mysql.connector.Error as err:
        print("Error:", err)
        return None

def get_balance(account_number):
    try:
        mycursor.execute("SELECT balance FROM Account WHERE account_number = %s", (account_number,))
        balance = mycursor.fetchone()
        if balance:
            return balance[0]  # Return the balance value
        else:
            return None  # Account not found or balance is None
    except mysql.connector.Error as err:
        print("Error:", err)
        return None  # Error occurred, return None

def update_balance(account_number, amount):
    try:
        mycursor.execute("UPDATE Account SET balance = balance + %s WHERE account_number = %s", (amount, account_number))
        mydb.commit()
        return True
    except mysql.connector.Error as err:
        print("Error:", err)
        return False

def insert_transaction(account_number, transaction_type, amount):
    try:
        mycursor.execute("INSERT INTO Transaction (account_number, transaction_type, amount) VALUES (%s, %s, %s)",
                         (account_number, transaction_type, amount))
        mydb.commit()
        return True
    except mysql.connector.Error as err:
        print("Error:", err)
        return False

def account_exists(account_number):
    try:
        mycursor.execute("SELECT account_number FROM Account WHERE account_number = %s", (account_number,))
        account = mycursor.fetchone()
        return account is not None
    except mysql.connector.Error as err:
        print("Error:", err)
        return False

# Deposit money route
@app.route('/deposit', methods=['POST'])
def deposit():
    if request.method == 'POST':
        if 'login_cust_id' in session:
            account_number = get_account_info(session['login_cust_id'])
            deposit_amount = float(request.form['deposit_amount'])
            if account_number:
                if update_balance(account_number, deposit_amount):
                    insert_transaction(account_number, 'deposit', deposit_amount)
                    message = "Deposit Successful"
                    return redirect(url_for('successful', message=message))
                else:
                    error_message = "Error occurred while depositing money. Please try again later."
                    return redirect(url_for('error', message=error_message))
            else:
                error_message = "No account found for the logged-in customer."
                return redirect(url_for('error', message=error_message))
        else:
            return redirect(url_for('login'))

# Withdraw money route
@app.route('/withdraw', methods=['POST'])
def withdraw():
    if request.method == 'POST':
        if 'login_cust_id' in session:
            account_number = get_account_info(session['login_cust_id'])
            withdraw_amount = float(request.form['withdraw_amount'])
            if account_number:
                # Get the current balance
                balance = get_balance(account_number)
                if balance is not None and balance >= withdraw_amount:
                    if update_balance(account_number, -withdraw_amount):
                        insert_transaction(account_number, 'withdrawal', withdraw_amount)
                        message = "Withdraw Successful"
                        return redirect(url_for('successful', message=message))
                    else:
                        error_message = "Error occurred while withdrawing money. Please try again later."
                        return redirect(url_for('error', message=error_message))
                else:
                    error_message = "Insufficient balance to withdraw."
                    return redirect(url_for('error', message=error_message))
            else:
                error_message = "No account found for the logged-in customer."
                return redirect(url_for('error', message=error_message))
        else:
            return redirect(url_for('login'))

# Transfer money route
@app.route('/transfer', methods=['POST'])
def transfer():
    if request.method == 'POST':
        if 'login_cust_id' in session:
            sender_account_number = get_account_info(session['login_cust_id'])
            recipient_account_number = int(request.form['recipient_account'])
            transfer_amount = float(request.form['transfer_amount'])
            if sender_account_number:
                sender_balance = get_balance(sender_account_number)
                if sender_balance is not None and sender_balance >= transfer_amount:
                    if account_exists(recipient_account_number):  # Check if recipient account exists
                        if update_balance(sender_account_number, -transfer_amount):
                            if update_balance(recipient_account_number, transfer_amount):
                                insert_transaction(sender_account_number, 'transfer', -transfer_amount)
                                insert_transaction(recipient_account_number, 'transfer', transfer_amount)
                                message = "Transfer Successful"
                                return redirect(url_for('successful', message=message))
                            else:
                                # Revert sender's balance if recipient's balance update fails
                                update_balance(sender_account_number, transfer_amount)
                                error_message = "Error occurred while transferring money. Please try again later."
                                return redirect(url_for('error', message=error_message))
                        else:
                            error_message = "Error occurred while transferring money. Please try again later."
                            return redirect(url_for('error', message=error_message))
                    else:
                        error_message = "Recipient account does not exist."
                        return redirect(url_for('error', message=error_message))
                else:
                    error_message = "Insufficient balance to transfer."
                    return redirect(url_for('error', message=error_message))
            else:
                error_message = "No account found for the logged-in customer."
                return redirect(url_for('error', message=error_message))
        else:
            return redirect(url_for('login'))

@app.route('/error')
def error():
    error_message = request.args.get('message', 'An error occurred.')
    return render_template('error.html', error=error_message)

def start_transaction():
    try:
        mydb.start_transaction()
    except mysql.connector.Error as err:
        print("Error:", err)

def commit_transaction():
    try:
        mydb.commit()
    except mysql.connector.Error as err:
        print("Error:", err)

def rollback_transaction():
    try:
        mydb.rollback()
    except mysql.connector.Error as err:
        print("Error:", err)

def check_active_loan(customer_id):
    try:
        # Check if there is any active loan for the given customer ID
        mycursor.execute("SELECT * FROM Loan WHERE customer_id = %s AND status = 'active'", (customer_id,))
        active_loan = mycursor.fetchone()
        return active_loan is not None
    except mysql.connector.Error as err:
        print("Error:", err)
        return False

def calculate_amount_payable(loan_amount, interest_rate, term_length):
    return loan_amount * (1 + (interest_rate / 100) * (term_length / 365))

@app.route('/loan', methods=['GET', 'POST'])
def loan():
    if request.method == 'POST':
        if 'login_cust_id' in session:
            customer_id = session['login_cust_id']
            
            # Retrieve form data
            amount = float(request.form['loan_amount'])
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            start_date = datetime.now().date()
            term_length = (end_date - start_date).days
            interest_rate = 5.0  # Example predefined interest rate

            # Fetch account number corresponding to customer ID
            account_number = get_account_info(customer_id)
            if not account_number:
                return "No account found for the logged-in customer."

            # Calculate amount payable
            amount_payable = calculate_amount_payable(amount, interest_rate, term_length)

            # Start a transaction
            start_transaction()

            try:
                # Insert into the loan table
                mycursor.execute("INSERT INTO Loan (customer_id, account_number, start_date, end_date, term_length, loan_amount, interest_rate, amount_payable, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                 (customer_id, account_number, start_date, end_date, term_length, amount, interest_rate, amount_payable, 'active'))

                # Update account balance
                if update_balance(account_number, amount):
                    # Add entry in the transaction table as deposit
                    insert_transaction(account_number, 'deposit', amount)
                    commit_transaction()
                    return render_template('loan_success.html')
                else:
                    # Rollback changes made to the loan table
                    rollback_transaction()
                    return "Error occurred while updating account balance."
            except mysql.connector.Error as err:
                # Rollback transaction if any error occurs
                rollback_transaction()
                print("Error:", err)
                return "Error occurred while processing the loan request. Please try again later."
        else:
            return redirect(url_for('login'))
    else:
        active_loan = check_active_loan(session['login_cust_id'])
        if active_loan:
            error_message = "You already have an active loan. You cannot take more loans."
            return redirect(url_for('error', message=error_message))
        
        interest_rate = 5.0  # Example predefined interest rate
        return render_template('loan.html', interest_rate=interest_rate)

@app.route('/loan_payment', methods=['POST'])
def loan_payment():
    if 'login_cust_id' in session:
        customer_id = session['login_cust_id']

        # Get loan details
        mycursor.execute("SELECT * FROM Loan WHERE customer_id = %s AND status = 'active'", (customer_id,))
        loan_details = mycursor.fetchone()

        if loan_details:
            amount_payable = loan_details[8]
            account_number = loan_details[2]

            # Check account balance
            account_balance = get_balance(account_number)

            if account_balance >= amount_payable:
                # Start a transaction
                start_transaction()

                try:
                    # Update account balance
                    if update_balance(account_number, -amount_payable):
                        # Add entry in the transaction table as withdrawal
                        insert_transaction(account_number, 'withdrawal', amount_payable)
                        # Update loan status to closed
                        mycursor.execute("UPDATE Loan SET status = 'closed' WHERE customer_id = %s AND status = 'active'", (customer_id,))

                        commit_transaction()
                        message = "Loan payment successful."
                        return redirect(url_for('successful', message=message))
                    else:
                        # Rollback changes made to the account balance
                        rollback_transaction()
                        return "Error occurred while updating account balance."
                except mysql.connector.Error as err:
                    # Rollback transaction if any error occurs
                    rollback_transaction()
                    print("Error:", err)
                    return "Error occurred while processing the loan payment. Please try again later."
            else:
                return "Not enough balance to make the loan payment."
        else:
            return "Loan details not found."
    else:
        return redirect(url_for('home'))

@app.route('/successful')
def successful():
    message = request.args.get('message', 'Successful.')
    return render_template('successful.html', success_msg=message)

if __name__ == '__main__':
    app.run(debug=True)
