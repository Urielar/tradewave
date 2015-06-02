from django.db import models
from django.contrib.auth.models import User


class AccountHolder(Entity):
    # total amount in USD of credits held
    total_amount = models.FloatField()

    # maximum amount of credits to issue
    max_credit_issued = models.FloatField()

    # maximum amount of credits that cam be held in account 
    max_credit_held = models.FloatField()

    class Meta:
        permissions = (
            ("credits_issue", "Can issue credits"),
            ("credits_transact", "Can transact in credits"),
        )    


# producer credit table
class Credit(models.Model):
    # unique user identifier
    credit_id = models.UUIDField(primary_key=True)

    # credit name as per issuer's choosing
    name = models.CharField(max_length=100)

    # credits are tied to entities
    issuer = models.ForeignKey(AccountHolder)
 
    # current credit generation (i.e. 6th time issued) 
    series = models.IntegerField()

    # total amount issued in USD 
    amount_issued = models.FloatField()

    # total amount redeemed to date in USD
    amount_redeemed = models.FloatField()
   
    # redeemed / issued (meaningful for comleted credit series)
    credit_rating = models.FloatField() 

    date_issued = models.DateTimeField('date issued')
    date_expire = models.DateTimeField('date to expire')
    date_lastspent = models.DateTimeField('date last transaction') 

    def __unicode__(self):
        return ' '.join([
            "credit",
            self.name,
            "series #",
            self.series,
            "issued by",
            self.issuer.name,
        ])


# user properties table
# we want to use Django's user object for authentication
class UserProperty(models.Model):
    # unique user identifier
    userid = models.UUIDField(primary_key=True)
 
    # reference to django's user object      
    user = models.OneToOneField(User, unique=True) 
    date_created = models.DateTimeField('date joined') 
    date_active = models.DateTimeField('date last active') 

    # personal id number
    pin = models.IntegerField()

    # represents a passive relationship with an entity
    # ('like', 'follow', etc) 
    favorites = models.ManyToManyField(Entity, through=Relationship)
 
    def __unicode__(self):
        return ' '.join([
            "user properties of",
            self.user.username,
        ])


# passive relationships ("like", "follow", etc)
class Relationship(models.Model):
    name = models.CharField(unique=True)
    user = models.ForeignKey(UserProperty)
    entity = models.ForeignKey(Entity)
 
    # date relationship commenced
    date_started = models.DateField()


# Entities are objects that can create and distribute credits. 
# For now this is only markets and vendors, but this could change in the future
class Entity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    date_created = models.DateTimeField()
    date_active = models.DateTimeField()
    venues = models.ManyToManyField(Venue, through=VenueMap)

    # entity reputation
    rating = models.FloatField()

    class Meta:
        abstract = True

        permissions = (
            ("entity_admin", "Can administer entity"),
            ("entity_manager", "Can manage entity"),
            ("entity_employee", "Is entity employee"),
        )    


# vendor table
class Vendor(Entity):
    industry = models.ForeignKey(Industry)

    # does vendor has a CSA
    is_csa = models.BooleanField()


# Type of business. (Food, Construction, Law, Medical, Etc.)    
class Industry(models.Model):
    name = models.CharField(max_length=64, unique=True)


# marketplace table
class Marketplace(Entity):
    # marketplaces are assigned to cities, but vendors are not
    city = models.ForeignKey(City) 

    # vendors that operate within the marketplace 
    vendors = models.ManyToManyField(Vendor, through='Affiliation') 

    def __unicode__(self):
        return ' '.join([
            "marketplace:",
            self.name,
            "in",
            self.city.name
        ])


# table that specifies the affiliation between a vendor and marketplace
class Affiliation(models.Model):
    marketplace = models.ForeignKey(Marketplace)
    vendor = models.ForeignKey(Vendor)
    date_started = models.DateField() # date affiliation began


# table that specifes amount of various credits held by account holders
class CreditMap(models.Model):
    holder = models.ForeignKey(AccountHolder)
    credit = models.ForeignKey(Credit)
    amount = models.FloatField()

    def __unicode__(self):
        return ' '.join([
            str(self.amount),
            "of",
            self.credit.name,
            "credits held by",
            self.holder.name,
        ]) 


# city (municipality) table
class City(models.Model):
    name = models.CharField(max_length=30)
    state = models.CharField(max_length=30)
    country = models.CharField(max_length=30)     

    class Meta:
        unique_together = ('name', 'state', 'country')

    def __unicode__(self):
        return ' '.join(['City:', self.name]) 


# venue table
class Venue(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    zipcode = models.CharField(max_length=5)
    city = models.ForeignKey(City)
    date_created = models.DateTimeField()
    date_active = models.DateTimeField()

    def __unicode__(self):
        return ' '.join([
            'Venue:',
            self.name,
            'at',
            self.city.name,
        ]) 


# transaction log table (record of all transactions)
class TransactionLog(models.Model):
    timestamp = models.DateTimeField("transaction timestamp")
    transact_from = models.ForeignKey(
        CreditMap,
        related_name="sender"
    )
    transact_to = models.ForeignKey(
        CreditMap,
        related_name="receiver"
    )
    amount = models.FloatField()
    venue = models.ForeignKey(Venue)

    # boolean flag to indicate whether the credit was
    # extinguished as a result of the transaction
    redeemed = models.BooleanField() 

    def __unicode__(self):
        return ' '.join([
            'Transaction:', 
            str(self.amount),
            self.transact_from.credit.name + "'s",
            "credits from",
            self.transact_from.holder.name,
            "sent to",
            self.transact_to.holder.name
        ]) 


# table that maps entities to venues
class VenueMap(models.Model):
    entity = models.ForeignKey(Entity)
    venue = models.ForeignKey(Venue)

    def __unicode__(self):
        return ' '.join([
            self.entity.name,
            "at",
            self.venue.name
        ])
