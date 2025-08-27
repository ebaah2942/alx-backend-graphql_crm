import graphene
from graphene_django import DjangoObjectType
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import datetime
from django.db import transaction
from crm.models import Customer, Product, Order
from graphene_django.filter import DjangoFilterConnectionField
from .filters import CustomerFilter, ProductFilter, OrderFilter
from crm.models import Product
import graphene
from crm.models import Order
from crm.models import Customer
from django.db.models import Sum



# -----------------------
# GraphQL Object Types
# -----------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)


# -----------------------
# CreateCustomer Mutation
# -----------------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    success = graphene.Boolean()
    message = graphene.String()
    customer = graphene.Field(CustomerType)

    def mutate(self, info, name, email, phone=None):
        # Email uniqueness check
        if Customer.objects.filter(email=email).exists():
            return CreateCustomer(success=False, message="Email already exists", customer=None)

        # Phone format validation
        if phone:
            phone_validator = RegexValidator(
                regex=r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$',
                message="Invalid phone format. Use +1234567890 or 123-456-7890."
            )
            try:
                phone_validator(phone)
            except Exception as e:
                return CreateCustomer(success=False, message=str(e), customer=None)

        customer = Customer(name=name, email=email, phone=phone)
        customer.save()

        return CreateCustomer(success=True, message="Customer created successfully", customer=customer)


# -----------------------
# BulkCreateCustomers Mutation
# -----------------------
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(CustomerInput, required=True)

    created_customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers):
        created = []
        errors = []

        # Use transaction for partial commit behavior
        with transaction.atomic():
            for data in customers:
                try:
                    # Email uniqueness
                    if Customer.objects.filter(email=data.email).exists():
                        errors.append(f"Email already exists: {data.email}")
                        continue

                    # Phone validation
                    if data.phone:
                        phone_validator = RegexValidator(
                            regex=r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$',
                            message=f"Invalid phone format for {data.email}"
                        )
                        phone_validator(data.phone)

                    customer = Customer(name=data.name, email=data.email, phone=data.phone)
                    customer.save()
                    created.append(customer)

                except Exception as e:
                    errors.append(f"{data.email if hasattr(data, 'email') else 'Unknown'}: {str(e)}")

        return BulkCreateCustomers(created_customers=created, errors=errors)


# -----------------------
# CreateProduct Mutation
# -----------------------
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    success = graphene.Boolean()
    message = graphene.String()
    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            return CreateProduct(success=False, message="Price must be positive", product=None)
        if stock < 0:
            return CreateProduct(success=False, message="Stock cannot be negative", product=None)

        product = Product(name=name, price=price, stock=stock)
        product.save()

        return CreateProduct(success=True, message="Product created successfully", product=product)


# -----------------------
# CreateOrder Mutation
# -----------------------
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.Int(required=True)
        product_ids = graphene.List(graphene.Int, required=True)
        order_date = graphene.DateTime(required=False)

    success = graphene.Boolean()
    message = graphene.String()
    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        # Validate customer
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(success=False, message="Invalid customer ID", order=None)

        # Validate products
        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            return CreateOrder(success=False, message="No valid products found", order=None)
        if len(products) != len(set(product_ids)):
            return CreateOrder(success=False, message="One or more product IDs are invalid", order=None)

        # Ensure at least one product
        if not product_ids:
            return CreateOrder(success=False, message="At least one product must be selected", order=None)

        total_amount = sum([p.price for p in products])

        order = Order(
            customer=customer,
            order_date=order_date or timezone.now(),
            total_amount=total_amount
        )
        order.save()
        order.products.set(products)

        return CreateOrder(success=True, message="Order created successfully", order=order)


# -----------------------
# Root Query Class
# -----------------------
class Query(graphene.ObjectType):
    customer = graphene.relay.Node.Field(CustomerType)
    product = graphene.relay.Node.Field(ProductType)
    order = graphene.relay.Node.Field(OrderType)

    all_customers = DjangoFilterConnectionField(CustomerType, order_by=graphene.List(of_type=graphene.String))
    all_products = DjangoFilterConnectionField(ProductType, order_by=graphene.List(of_type=graphene.String))
    all_orders = DjangoFilterConnectionField(OrderType, order_by=graphene.List(of_type=graphene.String))

    def resolve_all_customers(self, info, order_by=None, **kwargs):
        qs = Customer.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_products(self, info, order_by=None, **kwargs):
        qs = Product.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_orders(self, info, order_by=None, **kwargs):
        qs = Order.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs


# -----------------------
# Root Mutation Class
# -----------------------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        pass  # no arguments needed

    updated_products = graphene.List(ProductType)
    message = graphene.String()

    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated = []
        for product in low_stock_products:
            product.stock += 10  # simulate restocking
            product.save()
            updated.append(product)

        return UpdateLowStockProducts(
            updated_products=updated,
            message=f"{len(updated)} products restocked at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()



class Query(graphene.ObjectType):
    total_customers = graphene.Int()
    total_orders = graphene.Int()
    total_revenue = graphene.Float()

    def resolve_total_customers(root, info):
        return Customer.objects.count()

    def resolve_total_orders(root, info):
        return Order.objects.count()

    def resolve_total_revenue(root, info):
        return Order.objects.aggregate(total=Sum("totalamount"))["total"] or 0.0

schema = graphene.Schema(query=Query)    