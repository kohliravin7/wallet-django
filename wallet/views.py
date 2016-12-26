from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from rest_framework.renderers import JSONRenderer
from wallet.serialisers import WalletSerializer
from wallet.models import Wallet,Transaction, Userprofile
from django.db import transaction
from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse
from wallet.forms import UserForm, ProfileForm
from django.contrib import messages
from django.contrib.auth.models import User
# Create your views here.


def receive_money(request):
    username = request.GET.get("username", None)
    amount = request.GET.get("amount", None)
    wallet = Wallet.objects.get(username=username)
    wallet.add_money(int(amount))
    wallet.save()
    wallet = Wallet.objects.get(username=request.user.username)
    return render(request, 'user_profile.html', {'user': request.user,'userprofile': Userprofile.objects.get(user=request.user), 'wallet': wallet})


def add_money(request):
    if request.user:
        if request.POST and request.POST.get('amount'):
            username = request.user.username
            add_amount = request.POST.get('amount')
            wallet = Wallet.objects.get(username=username)
            wallet.add_money(add_amount)
            wallet.save()
            now = datetime.now()
            trans = Transaction(from_name=username, wallet_id=wallet, date=now, amount=add_amount)
            trans.save()
            return render(request, 'user_profile.html', {'user': request.user,'userprofile': Userprofile.objects.get(user=request.user), 'wallet': wallet})
        else:
            return render(request, 'add_money.html')
    else:
        return HttpResponseRedirect('/login/?next={}'.format('/add_money/'))


def subtract_money(request):
    if request.user:
        users = User.objects.all()
        users_ids = users.values_list('id', flat=True)
        users_list = []
        for id in users_ids:
            user = users.get(pk=id)
            if user.username != "ravinkohli" and user.username != request.user.username:
                users_list.append(user)
        if request.POST and request.POST.get('amount'):
            username = request.user.username
            withdraw = request.POST.get('amount')
            wallet = Wallet.objects.get(pk=request.user.userprofile.wallet_id_id)
            # if withdraw > wallet.amount:
            #     return render(request, 'send_money.html', {'error': 'Amount can not be greater than balance','users': users_list})
            wallet.subtract_money(withdraw)
            wallet.save()
            now = datetime.now()
            trans = Transaction(from_name=username, wallet_id=wallet,to=request.POST.get('receiver'), date=now, amount=withdraw)
            trans.save()
            print request.POST.get('receiver')
            return redirect('/receive/?username=%s&amount=%s' % (request.POST.get('receiver'), withdraw))
        else:
            return render(request, 'send_money.html',{'users': users_list})
    else:
        return HttpResponseRedirect('/login/?next={}'.format('/subtract_money/'))


@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        wallet = Wallet.objects.filter(username=request.user.username)
        request.user.userprofile.wallet_id = wallet.get()
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('/accounts/profile/')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.userprofile)
    return render(request, 'update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def user_profile(request):
    context = {}
    context['name'] = request.user.first_name + request.user.last_name
    context['wallet'] = request.user.userprofile.wallet_id
    context['transactions'] = Transaction.objects.filter(wallet_id=request.user.userprofile.wallet_id)
    if request.user.userprofile.date_ob:
        context['dob'] = request.user.userprofile.date_ob
    if request.user.userprofile.sex:
        context['sex'] = request.user.userprofile.sex
    return render(request, 'user_profile.html', context)


@login_required
def transaction(request):
    context = {}
    trans = Transaction.objects.filter(from_name=request.user.username)
    context['transaction'] = trans
    context['user'] = request.user
    return render(request, 'transaction.html', context)


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def wallet_list(request):
    if request.method == 'GET':
        wallets = Wallet.objects.all()
        serializer = WalletSerializer(wallets, many=True)
        return JSONResponse(serializer.data)


def wallet_detail(request, pk):
    """
    Retrieve, update or delete a code snippet.
    """
    try:
        wallet = Wallet.objects.get(pk=pk)
    except Wallet.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = WalletSerializer(wallet)
        return JSONResponse(serializer.data)
