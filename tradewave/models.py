from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


# defines city (municipality)
class City(models.Model):
    name = models.CharField(max_length=30)
    state = models.CharField(max_length=30)
    country = models.CharField(max_length=30)

    class Meta:
        unique_together = ('name', 'state', 'country')

    def __unicode__(self):
        return ' '.join(['City:', self.name])


# defines venue
class Venue(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=5)
    city = models.ForeignKey(City)

    # venue email
    email = models.EmailField()

    # created / updated timestamps
    date_created = models.DateTimeField('date created', auto_now_add=True)
    date_updated = models.DateTimeField('date last updated', auto_now=True)

    def __unicode__(self):
        return ' '.join([
            'Venue:',
            self.name,
            'at',
            self.city.name,
        ])


# defines entity
# Nota:
#   Entities are objects that can be either personal, vendors or marketplaces
#   Why do we need personal entities:
#       because credit accounts are linked to entities, not django user accounts.
#       So for each user that has a credit account we need an entity.
#       Personal entities are not allowed to issue credits.
#
#   A vendor or a marketplace entity are linked to one or more credit account(s).
#   Multiple users can manage an entity's credit account.
#   Credit accounts that are linked to a vendor or a marketplace entity are
#   capable of issues credits.
class Entity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    # contact email for the entity
    email = models.EmailField()

    # link to entity's credit account
    # Nota:
    #   If this is a personal entity associated with user's account, this will
    #   to user's personal credit Account
    #   If this is a vendor / marketplace entity, this will link to
    #   vendor's / markplace's credit account
    account = models.ForeignKey('Account')

    # can or cant not issue credits
    can_issue = models.BooleanField(default=False)

    # venues the entity is affiliated with
    venues = models.ManyToManyField(Venue, through='VenueMap')

    # entity reputation
    rating = models.FloatField(default=100.)

    # created / updated timestamps
    date_created = models.DateTimeField('date created', auto_now_add=True)
    date_updated = models.DateTimeField('date last updated', auto_now=True)

    class Meta:
        permissions = (
            ('entity_admin', 'Admin of entity'),
            ('entity_manager', 'Manager of entity'),
            ('entity_employee', 'Employee of entity'),
        )

    def __unicode__(self):
        return self.name


# define vendor
class Vendor(Entity):
    industry = models.ForeignKey('Industry')

    # does vendor has a CSA
    has_csa = models.BooleanField(default=False)

    # maximum amount of credits to issue (in USD)
    # can be used as a way to limit vendor's credit issuing ability
    # for now default is not to allow the vendors to issue credits
    max_credits_to_issue = models.DecimalField(decimal_places=2, default=0)


# define marketplace
class Marketplace(Entity):
    # physical location of the marketplace
    city = models.ForeignKey(City)

    # vendors that operate at the marketplace
    vendors = models.ManyToManyField(Vendor, through='Affiliation')

    def __unicode__(self):
        return ' '.join([
            'Marketplace',
            self.name,
            'located in',
            self.city.name
        ])


# defines registered users and their properties
# notes:
#   We use Django's built-in user object for authentication.
#   Every user has a personal credit account through their personal entity
#   A user can be affiliated with a number of vendors and/or marketplaces
class TradewaveUser(models.Model):
    # unique user identifier in Tradewave system
    uuid = models.UUIDField(primary_key=True)

    # reference to django's built-in user object
    user = models.OneToOneField(User, unique=True)

    # personal id number
    pin = models.PositiveSmallIntegerField()

    # qr image
    qr_image = models.ImageField(upload_to='qr')

    # user's personal entity
    entity_personal = models.OneToOneField(Entity)

    # vendor affiliation(s)
    vendors = models.ManyToManyField(Vendor, related_name='users', blank=True)

    # marketplace affiliation(s)
    marketplaces = models.ManyToManyField(Marketplace, related_name='users', blank=True)

    # represents a passive relationship with an entity
    # ('like', 'follow', etc)
    favorites = models.ManyToManyField(Entity, through='Relationship')

    # create / update timestamps
    date_created = models.DateTimeField('date joined', auto_now_add=True)
    date_updated = models.DateTimeField('date last updated', auto_now=True)

    class Meta:
        permissions = (
            ('credit_transact', 'Is allowed to make transactions'),
        )

    def __unicode__(self):
        return ' '.join([
            'User properties of',
            self.user.username,
        ])


# defines the credits issued
class Credit(models.Model):
    # unique credit identifier
    uuid = models.UUIDField(primary_key=True)

    # credits are issued by entities
    issuer = models.ForeignKey(Entity)

    # credit name (alias) as per issuer's choosing
    name = models.CharField(max_length=100)

    # current credit generation (i.e. 6th time issued)
    series = models.PositiveSmallIntegerField()

    # total amount issued (in USD)
    amount_issued = models.DecimalField(decimal_places=2)

    # total amount redeemed to date (in USD)
    amount_redeemed = models.DecimalField(decimal_places=2)

    # credit rating (e.g. redeemed / issued)
    credit_rating = models.FloatField()

    # various timestamps relevant to the issued credit
    date_created = models.DateTimeField('date issued', auto_now_add=True)
    date_updated = models.DateTimeField('date last updated', auto_now=True)

    def one_year_from_now():
        return timezone.now() + timedelta(days=365)

    # date of credit expiration (default is to expire in 1 year)
    date_expire = models.DateTimeField('date to expire', default=one_year_from_now)

    # date of last transaction using credit
    date_last_transacted = models.DateTimeField('date of last transaction')

    def __unicode__(self):
        return ' '.join([
            'Credit',
            self.name,
            'issued by',
            self.issuer.name,
            '(series #',
            self.series + ')'
        ])


# defines account(s) associated with an entity
class Account(models.Model):
    # account's wallet (collection of credits)
    wallet = models.ManyToManyField(Credit, through='CreditMap')

    # total amount credits held across all credits (in USD)
    amount_total = models.DecimalField(decimal_places=2)

    # create / update timestamps
    date_created = models.DateTimeField('date created', auto_now_add=True)
    date_last_transacted = models.DateTimeField('date last transacted', auto_now=True)

    def __unicode__(self):
        return ' '.join([
            'Credit account of entity',
            self.entity.name
        ])


# maps credits to accounts
class CreditMap(models.Model):
    account = models.ForeignKey(Account)
    credit = models.ForeignKey(Credit)
    amount = models.DecimalField(decimal_places=2)

    def __unicode__(self):
        return ' '.join([
            str(self.amount),
            'of',
            self.credit.name,
            'credits held by',
            self.account.entity.name,
        ])


# defines transaction log (record of all transactions)
class TransactionLog(models.Model):
    transact_from = models.ForeignKey(
        Account,
        related_name='transactions_sent'
    )
    transact_to = models.ForeignKey(
        Account,
        related_name='transactions_received'
    )

    # credit used in transaction
    credit = models.ForeignKey(Credit)

    # transaction amount (in USD)
    amount = models.DecimalField(decimal_places=2)

    # venue where transaction took place
    venue = models.ForeignKey(Venue)

    # boolean flag to indicate whether the credit was
    # extinguished as a result of the transaction
    redeemed = models.BooleanField(default=False)

    # date and time of transaction
    date_transacted = models.DateTimeField('transaction timestamp', auto_now_add=True)

    def __unicode__(self):
        return ' '.join([
            'Transaction in the amount of',
            str(self.amount),
            'in credit',
            self.credit.name,
            'from',
            self.transact_from.account.name,
            'to',
            self.transact_to.account.name
        ])


# maps entities to venues
class VenueMap(models.Model):
    entity = models.ForeignKey(Entity)
    venue = models.ForeignKey(Venue)

    def __unicode__(self):
        return ' '.join([
            'Entity',
            self.entity.name,
            'at venue',
            self.venue.name
        ])


# industry types
# (e.g. Food, Construction, Law, Medical, Etc.)
class Industry(models.Model):
    name = models.CharField(max_length=64, unique=True)


# define relationships
# (e.g. 'like', 'follow', etc)
class Relationship(models.Model):
    user = models.ForeignKey(TradewaveUser)
    entity = models.ForeignKey(Entity)
    name = models.CharField(unique=True, max_length=50)

    # create / update timestamps
    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)


# maps affiliations between a vendor and marketplace
class Affiliation(models.Model):
    marketplace = models.ForeignKey(Marketplace)
    vendor = models.ForeignKey(Vendor)

    # create / update timestamps
    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)
