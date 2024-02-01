from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.urls import reverse
from django.http import JsonResponse, Http404
from django.views.generic import View
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core import serializers
from .models import *
from tablib import Dataset
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.db.models import Max, Sum, Count
from faker import Faker
from django.core.exceptions import ObjectDoesNotExist
from channels.layers import get_channel_layer
from .consumers import ControlPanelConsumer
import json
from django.contrib import messages
from collections import defaultdict, OrderedDict
import math
from random import shuffle
from django.forms.models import model_to_dict


fake = Faker()

class Main(View):
    def get(self, request):
        qs = Statistic.objects.all()
        return render(request, 'event/main.html', {'qs': qs,})
    
    def post(self, request):
        new_stat = request.POST.get('new-statistic')
        obj, _ = Statistic.objects.get_or_create(name=new_stat)
        return redirect('dashboard', obj.slug)
    
class Dashboard(View):
    def get(self, request, slug):
        obj = get_object_or_404(Statistic, slug=slug)
        context = {
            'name': obj.name,
            'slug': obj.slug,
            'data': obj.data,
            'user': request.user.username if request.user.username else fake.name()
        }
        return render(request, 'event/dashboard.html', context)
    
class ChartData(View):
    def get(self, request, slug):
        obj = get_object_or_404(Statistic, slug=slug)
        qs = obj.data.values('owner').annotate(Sum('value'))
        chart_data = [x["value__sum"] for x in qs]
        chart_labels = [x["owner"] for x in qs]
        return JsonResponse({
            "chartData": chart_data,
            "chartLabels": chart_labels,
        })
        
class Home(View):
    def get(self, request):
        return render(request, 'home.html')

class Login(View):
    def get(self, request):
        return render(request, 'login.html')
    
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if hasattr(user, 'jury'):
                tatami = Tatami.objects.filter(id_jury=user.jury).first()
                print(tatami)
                if tatami:
                    event = Event.objects.filter(id_tatami=tatami).first()
                    event_slug = event.slug
                    tatami_pk = tatami.pk
                    return redirect('jurypanel1', event_slug=event_slug, tatami_pk=tatami_pk)
            return redirect('home')
        else:
            return render(request, 'login.html')

class Logout(View):
    def get(self, request):
        logout(request)
        return render(request, 'home.html')

class listEvent(View):
    def get(self, request):
        event = Event.objects.all()
        context = {
            'event': event,
        }
        return render(request, 'event.html', context)

class detailEvent(View):
    def get(self, request, slug, jenis):
        event = get_object_or_404(Event, slug=slug)
        
        if jenis == 'kata':
            bagan = event.id_bagan.filter(kategori='kata').order_by('-pk')
            tipe = 'kata'
        elif jenis == 'kumite':
            bagan = event.id_bagan.filter(kategori='kumite') 
            tipe = 'kumite'  

        context =  {
            'event': event,
            'bagan': bagan,
            'tipe': tipe,
        }
        return render(request, 'detailevent.html', context)
    
class BaganView(View):
    def get(self, request, slug, jenis, bagan_pk):
        event = get_object_or_404(Event, slug=slug)
        bagan = event.id_bagan.get(pk=bagan_pk)
        
        if jenis == 'kata':
            # if bagan.id_detailbagan.first().id_atlet.count() == 2:
            if bagan.new != True:
                detailbagan1 = bagan.id_detailbagan.get(perebutanjuara=1)
                detailmedali1 = DetailMedali.objects.filter(id_detailbagan=detailbagan1).order_by('number')
                detailbagan2 = bagan.id_detailbagan.get(perebutanjuara=3)
                detailmedali2 = DetailMedali.objects.filter(id_detailbagan=detailbagan2).order_by('number')
                detailbagan3 = bagan.id_detailbagan.get(perebutanjuara=4)
                detailmedali3 = DetailMedali.objects.filter(id_detailbagan=detailbagan3).order_by('number')
            else:
                round_1 = bagan.id_detailbagan.filter(perebutanjuara=5).order_by('group_tanding')
                round_2 = bagan.id_detailbagan.filter(perebutanjuara=4).order_by('group_tanding')
                round_3 = bagan.id_detailbagan.filter(perebutanjuara=3).order_by('group_tanding')
                round_4 = bagan.id_detailbagan.filter(perebutanjuara=2).order_by('group_tanding')
                round_5 = bagan.id_detailbagan.filter(perebutanjuara=1).order_by('group_tanding').first()
            tipe = 'kata'

        elif jenis == 'kumite':
            tipe = 'kumite'  

        # if bagan.id_detailbagan.first().id_atlet.count() == 2:
        if bagan.new != True:
            context =  {
                'event': event,
                'bagan': bagan,
                'tipe': tipe,
                'detailbagans': detailbagan1,
                'detailmedali1': detailmedali1,
                'detailmedali2': detailmedali2,
                'detailmedali3': detailmedali3,
                }
        else:
            context =  {
                'event': event,
                'bagan': bagan,
                'tipe': tipe,
                'round_1': round_1,
                'round_2': round_2,
                'round_3': round_3,
                'round_4': round_4,
                'round_5': round_5,
            }
        # else:
        #     print('hlskdjfkljsdf')
        #     print(bagan.id_detailbagan.first().id_atlet.count())
        #     print(bagan.id_detailbagan.first().pk)
        #     context =  {
        #         'event': event,
        #         'bagan': bagan,
        #         'tipe': tipe,
        #     }
        return render(request, 'baganview.html', context)
    
class kelEvent(View):
    def get(self, request):
        event = Event.objects.all()
        context = {
            'event': event,
        }
        return render(request, 'kelevent.html', context)

class keldetailEvent(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        kata = event.id_bagan.filter(kategori='kata')
        kumite = event.id_bagan.filter(kategori='kumite')
        context =  {
            'event': event,
            'kata': kata,
            'kumite': kumite,
            'bagan_kategori': bagan_kategori,
            'tatami': tatami,
        }
        return render(request, 'event/index.html', context)
    
class keldetailKata(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
        kata = event.id_bagan.filter(kategori='kata')
        context = {
            'event': event,
            'kata': kata,
            'bagan_kategori': bagan_kategori,
        }
        return render(request, 'event/kelkata.html', context)

class KumiteHome(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        kumitebagans = BaganKumiteDetail.objects.filter(atlet2__isnull=False).order_by('?')
        kumitebagans2 = BaganKumiteDetail.objects.filter(atlet2__isnull=True)
        judul_kumite = PoolBaganKumite.objects.first()
        bagankumites = Bagan.objects.filter(event=event, kategori='kumite').order_by('-pk')
        kategoris = BaganKategori.objects.all()

        round2_num = math.ceil(kumitebagans.count()/2)
        round2 = []

        round3_num = math.ceil(round2_num/2)
        round3 = []

        round4_num = math.ceil(round3_num/2)
        round4 = []

        round5_num = math.ceil(round4_num/2)
        round5 = []

        for i in range(1, math.ceil(kumitebagans.count()/2) + 1):
            round2.append(i)

        for i in range(1, round3_num + 1):
            round3.append(i) 

        for i in range(1, round4_num + 1):
            round4.append(i) 

        for i in range(1, round5_num + 1):
            round5.append(i) 

        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'tatami': tatami,
            'bagans': kumitebagans,
            'bagans2': kumitebagans2,
            'round2': round2,
            'round3': round3,
            'round4': round4,
            'round5': round5,
            'judul': judul_kumite,
            'kategoris': kategoris,
            'bagan_kumites': bagankumites,
        }
        return render(request, 'event/kumite.html', context)

    def post(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan = event.id_bagan.all()
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        type = request.POST.get('type')

        if type == "reset":
            BaganKumiteDetail.objects.all().delete()
            AtletKumite.objects.all().delete()
            return redirect('kumite-home', slug=slug)
        
        elif type == "nama":
            judul = request.POST.get('judul')
            judul_kumite = PoolBaganKumite.objects.first()
            judul_kumite.judul = judul
            print(judul_kumite.judul)
            judul_kumite.save()
            return redirect('kumite-home', slug=slug)
        
        else:
            dataset = Dataset()

            new_data = request.FILES['file'] 

            imported_data = dataset.load(new_data.read(), format='xlsx')

            
            for data in imported_data:
                if len(data) >= 1:
                    name = data[0]
                    info = data[1].upper()
                    subinfo = data[2].upper()

                    atlet = AtletKumite(
                        nama_atlet=name,
                        info=info,
                        subinfo=subinfo,
                    )

                    atlet.save()

                    # if BaganKumiteDetail.objects.all().count() != 0:
                    #     detailkumites = BaganKumiteDetail.objects.filter(atlet2__isnull=True)
                    #     if detailkumites.count() >= 1:
                    #         for i in detailkumites:
                    #             if i.atlet2 is None:
                    #                 if i.atlet1.info != atlet.info:
                    #                     i.atlet2 = atlet
                    #                     i.save()
                    #                     break
                    #                 elif detailkumites.count() >= 2:
                    #                     i.atlet2 = atlet
                    #                     i.save()
                    #                     break
                    #                 else:
                    #                     BaganKumiteDetail.objects.create(atlet1=atlet)
                    #                     break
                    #     else:
                    #         BaganKumiteDetail.objects.create(atlet1=atlet)
                    # else:
                    #     BaganKumiteDetail.objects.create(atlet1=atlet)

            atlet_list = list(AtletKumite.objects.all())
            shuffle(atlet_list)  # Shuffle the list to randomize the pairs

            while len(atlet_list) >= 2:
                atlet1 = atlet_list.pop()
                atlet2 = None

                # Find an athlete with a different info
                for atlet in atlet_list:
                    if atlet.info != atlet1.info:
                        atlet2 = atlet
                        atlet_list.remove(atlet)
                        break

                # If no athlete with different info is found, pair them with the same info
                if atlet2 is None:
                    atlet2 = atlet_list.pop()

                # Create BaganKumiteDetail instance
                BaganKumiteDetail.objects.create(atlet1=atlet1, atlet2=atlet2)

            # Handle the case when there's an odd number of athletes left
            if atlet_list:
                # Pair the remaining athlete with an athlete with the same info
                atlet1 = atlet_list.pop()
                atlet2 = next((atlet for atlet in atlet_list if atlet.info == atlet1.info), None)
                if atlet2:
                    atlet_list.remove(atlet2)
                    BaganKumiteDetail.objects.create(atlet1=atlet1, atlet2=atlet2)

        return redirect('kumite-home', slug=slug)

class KumiteControlPanel(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan = event.id_bagan.all()
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'tatami': tatami,
        }
        return render(request, 'event/kumite-cp.html', context)
    
class keldetailAtlet(View):
    def get(self, request, slug, jenis_kelamin=None):
        event = get_object_or_404(Event, slug=slug)
        bagan = event.id_bagan.all()
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        jk = 'all'
    
        if jenis_kelamin == 'putra':
            atlet_putra = event.id_atlet.filter(jenis_kelamin='putra')
            atlet_putri = None
            jk = 'putra'
        elif jenis_kelamin == 'putri':
            atlet_putri = event.id_atlet.filter(jenis_kelamin='putri')
            atlet_putra = None
            jk = 'putri'
        else:
            atlet_putra = event.id_atlet.filter(jenis_kelamin='putra')
            atlet_putri = event.id_atlet.filter(jenis_kelamin='putri')
            
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'jk': jk,
            'tatami': tatami,
        }
        return render(request, 'event/atlet.html', context)
    
    def post(self, request, slug, jenis_kelamin=None): # import atlet
        form_type = request.POST.get('submit_button')

        if form_type == 'importatlet':
            dataset = Dataset()
            new_data = request.FILES['file'] 
            if not new_data.name.endswith('.xlsx'):
                messages.error(request, 'Invalid file format. Please upload an Excel file.')
                return redirect('keldetailatlet', slug=slug)

            imported_data = dataset.load(new_data.read(), format='xlsx')
            
            event = Event.objects.get(slug=slug)
            bagan = Bagan.objects.filter(event=event)

            for data in imported_data:
                if len(data) >= 1:
                    nama_atlet = data[0]
                    jenis_kelamin = data[1].lower()
                    perguruan = data[2]
                    perwakilan = data[3]
                    nomor_tanding = data[4]
                    tipe = data[5]
                    atlet = Atlet(
                        nama_atlet=nama_atlet,
                        jenis_event='internal',
                        jenis_kelamin=jenis_kelamin,
                        perguruan=perguruan,
                        nomor_tanding=f'{nomor_tanding} - {tipe}',
                        perwakilan=perwakilan,
                        tipe=tipe,
                    )
                    atlet.save()
                    event.id_atlet.add(atlet)

                    validate = BaganKategori.objects.filter(event=event, judul_kategori=f'{nomor_tanding} - {tipe}').first()

                    if validate is None:
                        createdkategori = BaganKategori.objects.create(judul_kategori=f'{nomor_tanding} - {tipe}', tipe=tipe)
                        createdkategori.id_atlet.add(atlet.pk)
                        atlet.nomor_tanding = createdkategori.judul_kategori
                        atlet.save()
                        # atlet.nomor_tanding = createdkategori.judul_kategori
                        event.bagan_kategori.add(createdkategori)
                    else:
                        validate.id_atlet.add(atlet.pk)

            messages.success(request, 'Data telah sukses di import')
            return redirect('keldetailatlet', slug=slug)
        
        elif form_type == 'tambahatlet':
            nama_atlet = request.POST.get('nama_atlet').upper()
            jenis_kelamin = request.POST.get('jenis_kelamin').lower()
            perguruan = request.POST.get('perguruan').upper()
            perwakilan = request.POST.get('perwakilan').upper()
            nomor_tanding = request.POST.get('nomor_tanding')
            tipe = request.POST.get('tipe')

            event = Event.objects.get(slug=slug)

            if jenis_kelamin == "-" or nomor_tanding == "-" or tipe == "-":
                messages.success(request, 'Ada data yang tidak di isi')
                return redirect('keldetailatlet', slug=slug)
            else:
                atlet = Atlet(
                    nama_atlet=nama_atlet,
                    jenis_event='internal',
                    jenis_kelamin=jenis_kelamin,
                    perguruan=perguruan,
                    perwakilan=perwakilan,
                    nomor_tanding=nomor_tanding,
                    tipe=tipe,
                )
                atlet.save()
                event.id_atlet.add(atlet)

                validate = BaganKategori.objects.filter(judul_kategori=nomor_tanding).first()

                if validate is None:
                    createdkategori = BaganKategori.objects.create(judul_kategori=f'{nomor_tanding}', tipe=tipe)
                    createdkategori.id_atlet.add(atlet.pk)
                    event.bagan_kategori.add(createdkategori)
                else:
                    validate.id_atlet.add(atlet.pk)

                messages.success(request, 'Berhasil menambah atlet')
                return redirect('keldetailatlet', slug=slug)
        elif form_type == 'hapusatlet':
            atlet_pk = request.POST.get("atlet_pk")
            atlet = Atlet.objects.get(id_atlet=atlet_pk)
            atlet.delete()

            messages.success(request, 'Berhasil menghapus atlet')
            return redirect('keldetailatlet', slug=slug)
        else:
            messages.success(request, 'Error')
            return redirect('keldetailatlet', slug=slug)
        
class AtletEdit(View):
    def get(self, request, slug, atlet_pk):
        event = get_object_or_404(Event, slug=slug)
        bagan_kategoris = BaganKategori.objects.filter(event=event)
        atlet = get_object_or_404(Atlet, pk=atlet_pk)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        atlet_edit = True

        context = {
            'event': event,
            'atlet': atlet,
            'bagan_kategoris': bagan_kategoris,
            'atlet_edit': atlet_edit,
            'bagan_kategori': bagan_kategori,
            'tatami': tatami,
        }
        return render(request, 'event/atletedit.html', context)
    
    def post(self, request, slug, atlet_pk):
        event = get_object_or_404(Event, slug=slug)
        bagan_kategoris = BaganKategori.objects.filter(event=event)
        atlet = get_object_or_404(Atlet, pk=atlet_pk)

        atlet.nama_atlet = request.POST.get('nama').upper()
        atlet.perguruan = request.POST.get('perguruan').upper()
        atlet.perwakilan = request.POST.get('perwakilan').upper()
        atlet.jenis_kelamin = request.POST.get('jenis_kelamin').lower()
        nomor_tanding_atlet = request.POST.get('nomor_tanding')
        atlet.nomor_tanding = nomor_tanding_atlet

        unedited_bagan_kategori = event.bagan_kategori.all()
        for bagan_kategori in unedited_bagan_kategori:
            bagan_kategori.id_atlet.remove(atlet)

        bagan_kategori = BaganKategori.objects.filter(event=event, judul_kategori=nomor_tanding_atlet).first()
        bagan_kategori.id_atlet.add(atlet)
        atlet.save()

        messages.success(request, 'Atlet telah berhasil di edit.')
        return redirect('keldetailatlet', slug=slug)
    
class keldetailTatami(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan = event.id_bagan.all()
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        tatamis = event.id_tatami.all()
        
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'tatamis': tatamis,
            'tatami': tatami,
        }
        return render(request, 'event/tatami.html', context)
    
    def post(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        form_type = request.POST.get('submit_button')

        if form_type == 'tambah':
            if event.id_tatami.exists():
                max_number = event.id_tatami.aggregate(Max('number'))['number__max']
                
                if max_number:
                    tatami_number = max_number + 1
                else:
                    tatami_number = 1
            else:
                tatami_number = 1

            tatami = Tatami.objects.create(tatami=f'Tatami {tatami_number}', number=tatami_number)
            event.id_tatami.add(tatami)
            
            adm_tatami = f'admtatami{tatami_number}'

            admin_tatami_user = User.objects.create_user(username=adm_tatami, password=adm_tatami)
            admin_tatami = AdminTatami.objects.create(id_user=admin_tatami_user)
            tatami.admin = admin_tatami
            tatami.save()
            admin_tatami.save()

            for i in range(7):
                username = f"j{i+1}t{tatami_number}" 
                user = User.objects.create_user(username=username, password=username)
                jury = Jury.objects.create(id_user=user)
                tatami.id_jury.add(jury)
                jury.number = f'{i+1}'
                jury.save()

        elif form_type == 'hapus':
            tatami_pk = request.POST.get('tatami')
            tatami_obj = Tatami.objects.get(pk=tatami_pk)
            tatami_obj.delete()
            

        return redirect('keldetailtatami', slug=slug)

class keldetailTatamiEdit(View):
    def get(self, request, slug, tatami_pk):
        event = get_object_or_404(Event, slug=slug)
        bagans = event.id_bagan.filter(tatami=tatami_pk)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        bagan_kategoris = event.bagan_kategori.all()
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
        bagan_kategori_choices = bagan_kategoris.filter(tatami_nomor_tanding=None)
        bagan_kategori_tatami = bagan_kategoris.filter(tatami_nomor_tanding=tatami_pk)
        tatamis = event.id_tatami.all()
        tatami = event.id_tatami.get(pk=tatami_pk)

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'bagan_kategori_choices': bagan_kategori_choices,
            'bagan_kategori_tatami': bagan_kategori_tatami,
            'tatamis': tatamis,     
            'tatami': tatami,
            'bagans': bagans,
            'tempat': 'edit',
        }
        return render(request, 'event/tatamiedit.html', context)
    
    def post(self, request, slug, tatami_pk):
        form_type = request.POST.get('submit_button')
        if form_type == 'hapus_bagan_kategori':
            bagan_kategori = request.POST.get('bagan_kategori_pk')
            bagan_kategori_obj = BaganKategori.objects.get(pk=bagan_kategori)
            bagan_kategori_obj.tatami_nomor_tanding = None
            bagan_kategori_obj.save()
        else:
            bagan_kategori_pk = request.POST.get('data')
            if bagan_kategori_pk == '-':
                pass
            else:
                tatami = Tatami.objects.get(pk=tatami_pk)
                bagan_kategori_pk = BaganKategori.objects.get(pk=bagan_kategori_pk)
                bagan_kategori_pk.tatami_nomor_tanding = None
                bagan_kategori_pk.tatami_nomor_tanding = tatami
                bagan_kategori_pk.save()
        return redirect('keldetailtatamiedit', slug=slug, tatami_pk=tatami_pk)

class kelinternalAtlet(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan_kategori = event.bagan_kategori.all()
        atlet_putra = event.id_atlet.filter(jenis_kelamin='putra', jenis_event='internal')
        atlet_putri = event.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
        }
        return render(request, 'event/atlet.html', context)

class GeneratePDF(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        bagan = get_object_or_404(Bagan, id_bagan=pk)
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)

        if bagan.tipe:
            detail_bagan = bagan.id_detailbagan.order_by('-id_score__id_totalscore__total')

            detail_bagan_ids = [detail_bagan for detail_bagan in detail_bagan]

            detail_medali_list = DetailMedali.objects.filter(id_detailbagan__in=detail_bagan_ids)

            midpoint = len(detail_medali_list) // 2

            pairs_list = []

            for i in range(0, len(detail_medali_list), 2):
                if i + 1 < len(detail_medali_list):
                    pairs_list.append((detail_medali_list[i], detail_medali_list[i + 1]))
                else:
                    pairs_list.append((detail_medali_list[i], None))

            distinct_groups = detail_bagan.values('group_tanding').annotate(group_count=Count('group_tanding')).count()

            middle_group = distinct_groups // 2

            set1 = list(range(1, middle_group + 1))
            set2 = list(range(middle_group + 1, distinct_groups + 1))

            grouped_data = defaultdict(list)
            
            for item in detail_bagan:
                grouped_data[item.group_tanding].append(item)

            grouped_data_list = OrderedDict(sorted(grouped_data.items()))

            group_value = int(distinct_groups)
            group_values = list(range(1, group_value + 1))

            tatami = event.id_tatami.all()

            try:
                admintatami = Tatami.objects.get(admin__id_user=request.user)

            except ObjectDoesNotExist:
                admintatami = None
                messages.error(request, "Akun ini tidak memiliki tatami.")
                    
            atlet_list = []
            for detail in detail_bagan:
                atlet_list.extend(detail.id_atlet.all())
            

            for i in detail_bagan:
                ahh = i.id_scoredetail.filter(number=1)
                ahh1 = ahh.count()
                # for j in i.id_scoredetail.all():
                #     ahh = i.id_scoredetail.count()
                #     print(ahh)
            
            context = {
                'event': event,
                'bagan_kategori': bagan_kategori,
                'bagan': bagan,
                'detail_bagan': detail_bagan,
                'kategori': kategori,
                'atlet_list': atlet_list,
                'tatami': tatami,
                'admintatami' : admintatami,
                'group_value': group_value,
                'group_values': group_values,
                'grouped_data': grouped_data_list,
                'set1': set1,
                'set2': set2,
                # 'matchup_list': matchup_list,
                'detail_bagan_ids': detail_bagan_ids,
                'detail_medali_list': detail_medali_list,
                'pairs_list': pairs_list,
                # 'first_half_list': first_half_list,
                # 'second_half_list': second_half_list,
            }
        else:
            perebutan1 = bagan.id_detailbagan.get(perebutanjuara=1)
            atlet_perebutan1 = DetailMedali.objects.filter(id_detailbagan=perebutan1)
            try:
                atlet1aka_detail_score = perebutan1.id_score.first().juri_score.filter(number=1)
                atlet1ao_detail_score = perebutan1.id_score.first().juri_score.filter(number=2)
            except AttributeError:
                atlet1aka_detail_score = ['', '', '', '', '']
                atlet1ao_detail_score = ['', '', '', '', '']

            perebutan2 = bagan.id_detailbagan.get(perebutanjuara=2)
            atlet_perebutan2 = DetailMedali.objects.filter(id_detailbagan=perebutan2)
            try:
                atlet2aka_detail_score = perebutan2.id_score.first().juri_score.filter(number=1)
                atlet2ao_detail_score = perebutan2.id_score.first().juri_score.filter(number=2) 
            except AttributeError:
                atlet2aka_detail_score = ['', '', '', '', '']
                atlet2ao_detail_score = ['', '', '', '', '']

            perebutan3 = bagan.id_detailbagan.get(perebutanjuara=3)
            atlet_perebutan3 = DetailMedali.objects.filter(id_detailbagan=perebutan3)
            try:
                atlet3aka_detail_score = perebutan3.id_score.first().juri_score.filter(number=1)
                atlet3ao_detail_score = perebutan3.id_score.first().juri_score.filter(number=2) 
            except AttributeError:
                atlet3aka_detail_score = ['', '', '', '', '']
                atlet3ao_detail_score = ['', '', '', '', '']   

            perebutan4 = bagan.id_detailbagan.get(perebutanjuara=4)
            atlet_perebutan4 = DetailMedali.objects.filter(id_detailbagan=perebutan4)
            try:
                atlet4aka_detail_score = perebutan4.id_score.first().juri_score.filter(number=1)
                atlet4ao_detail_score = perebutan4.id_score.first().juri_score.filter(number=2) 
            except AttributeError:
                atlet4aka_detail_score = ['', '', '', '', '']
                atlet4ao_detail_score = ['', '', '', '', '']    

            context = {
                'event': event,
                'bagan_kategori': bagan_kategori,
                'bagan': bagan,
                'kategori': kategori,
                'perebutan1': perebutan1,
                'atlet_perebutan1': atlet_perebutan1,
                'atlet1aka_detail_score': atlet1aka_detail_score,
                'atlet1ao_detail_score': atlet1ao_detail_score,
                'perebutan2': perebutan2,
                'atlet_perebutan2': atlet_perebutan2,
                'atlet2aka_detail_score': atlet2aka_detail_score,
                'atlet2ao_detail_score': atlet2ao_detail_score,
                'perebutan3': perebutan3,
                'atlet_perebutan3': atlet_perebutan3,
                'atlet3aka_detail_score': atlet3aka_detail_score,
                'atlet3ao_detail_score': atlet3ao_detail_score,
                'perebutan4': perebutan4,
                'atlet_perebutan4': atlet_perebutan4,
                'atlet4aka_detail_score': atlet4aka_detail_score,
                'atlet4ao_detail_score': atlet4ao_detail_score,
            }
        return render(request, 'event/index-pdf.html', context)  
    
class kelexternalAtlet(View):
    def get(self, request, slug):
        event = get_object_or_404(Event, slug=slug)
        bagan_kategori = event.bagan_kategori.all()
        atlet_putra = event.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
        atlet_putri = event.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
        }
        return render(request, 'event/atlet.html', context)

class keldetailKategori(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        event = get_object_or_404(Event, slug=event_slug)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri')

        bagan = event.id_bagan.filter(kategori_kata=kategori, jenis_kelamin=jenis_kelamin).order_by('-tanggal_dibuat')

        print('test')

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'bagan': bagan,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'tatami': tatami,
        }
        return render(request, 'event/kategorikata.html', context)

    def post(self, request, event_slug, kategori_slug, jenis_kelamin):
        form_type = request.POST.get('form_type')
        form_type1 = request.POST.get('group1_submit')

        print('JKHFKASDHFKASJFKAJSDKFALKSJF')

        if form_type1 == 'tambahbagan':
            groups = request.POST.get('groups')
            penilaian_juri = request.POST.get('juri')

            group_value = int(groups)
            group_values = list(range(1, group_value + 1))

            team_values = {}
            team_kata = {}
            
            for i in group_values:
                team_values[i] = request.POST.getlist(f'team{i}')
                print(team_values[i])
                team_kata[i] = request.POST.getlist(f'team{i}kata')

            ranking = request.POST.get('ranking')

            event = get_object_or_404(Event, slug=event_slug)
            bgn_kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
            jenis_kelamin_display = dict(Atlet.JENIS_KELAMIN).get(jenis_kelamin)
            
            is_external = 'external' in request.path  
            
            counter = 0
            group = chr(ord('1') + counter)

            url_condition = 'External' if is_external else 'Internal'
            
            while Bagan.objects.filter(judul_bagan__icontains=f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Penyisihan {group} - {url_condition}').exists():
                counter += 1
                group = chr(ord('1') + counter)

            judul_bagan = f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Penyisihan {group} - {url_condition}'
            if url_condition == 'External':
                bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='external', banyaknya_juri=penilaian_juri)
            else:
                bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='internal', banyaknya_juri=penilaian_juri)
                
            event.id_bagan.add(bagan)
            bagan.kategori_kata.set([bgn_kategori])

            if 'group1_submit' in request.POST:
                for j in group_values:
                    for i in range(len(team_values[j])):
                        if team_values[j]:
                            detail_bagan = DetailBagann.objects.create(round=1)
                            detail_bagan.group_tanding = j
                            bagan.id_detailbagan.add(detail_bagan)
                            for atlet_id in [team_values[j][i]]:
                                if atlet_id:
                                    try:
                                        atlet = Atlet.objects.get(id_atlet=atlet_id)
                                        detail_bagan.id_atlet.add(atlet)
                                        detail_bagan.save()
                                        print(atlet_id)
                                    except Atlet.DoesNotExist:
                                        pass
                                else:
                                    print('Nama atlet tidak ada...')

                bagan.tipe = "Ranking"
                bagan.save()
                return redirect('keldetailkategori', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin)
            
            else:
                print('safjlaskd')
            
            return redirect('keldetailkategori', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin)

        elif form_type == 'tambahbaganform':
            grup_value = request.POST.get('value')
            juri_value = request.POST.get('juri')

            grup_value = int(grup_value)
            grup_values = list(range(1, grup_value + 1))

            midpoint = len(grup_values) // 2

            # Divide the list into set1 and set2
            set1 = grup_values[:midpoint]
            set2 = grup_values[midpoint:]

            num_loops1 = [1, 2, 3, 4]
            num_loops2 = [1, 2, 3]
            num_loops3 = [1, 2]
            event = get_object_or_404(Event, slug=event_slug)
            bagan = event.id_bagan.all()
            bagan_kategori = event.bagan_kategori.all()
            kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
            atlet_putra_internal = kategori.id_atlet.filter(event=event, jenis_kelamin='putra', jenis_event='internal')
            atlet_putri_internal = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
            atlet_putra_external = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
            atlet_putri_external = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')

            # Get the URL for putra internal
            putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
            putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
            putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
            putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
            url_parts = request.path.split('/')
            internal = 'internal' in url_parts
            external = 'external' in url_parts

            context = {
                'event': event,
                'bagan_kategori': bagan_kategori,
                'kategori': kategori, 
                'atlet_putra_internal': atlet_putra_internal,
                'atlet_putri_internal': atlet_putri_internal,
                'atlet_putra_external': atlet_putra_external,
                'atlet_putri_external': atlet_putri_external,
                'putrainternal_url': putrainternal_url,
                'putriinternal_url': putriinternal_url,
                'putraexternal_url': putraexternal_url,
                'putriexternal_url': putriexternal_url,
                'internal': internal,
                'external': external,
                'num_loops1': num_loops1,
                'num_loops2': num_loops2,
                'num_loops3': num_loops3,
                'grup_value': grup_value,
                'grup_values': grup_values,
                'juri_value': juri_value,
                'set1': set1,
                'set2': set2,
            }
            return render(request, 'event/tambahbagan.html', context)
        

def deletebagan(request, event_slug, kategori_slug, jenis_kelamin, bagan_pk):
    try:
        object_to_delete = Bagan.objects.get(pk=bagan_pk)
    except Bagan.DoesNotExist:
        raise Http404("Object does not exist")
    
    # Check if the object belongs to the specific event, category, and gender (jenis_kelamin)
    try:
        event = Event.objects.get(slug=event_slug, id_bagan__pk=bagan_pk)
    except Event.DoesNotExist:
        raise Http404("Event not found")
    
    # Check if the event is associated with the specific category
    if not event.bagan_kategori.filter(slug=kategori_slug).exists():
        raise Http404("Event not associated with this category")
    
    # Delete the object
    object_to_delete.delete()
    
    return redirect("keldetailkategori", event_slug, kategori_slug, jenis_kelamin)

class BaganEdit(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk):
        event = get_object_or_404(Event, slug=event_slug)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri')

        bagan = Bagan.objects.get(pk=bagan_pk)
        print(bagan.pk)

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'bagan': bagan,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'tatami': tatami,
        }
        return render(request, 'event/bagan-edit.html', context)

    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk):
        banyaknya_juri = int(request.POST.get('juri'))
        bagan = Bagan.objects.get(pk=bagan_pk)
        bagan.banyaknya_juri = banyaknya_juri
        bagan.save()
        return redirect('keldetailkategori', event_slug, kategori_slug, jenis_kelamin)
    
class keldetailBagan(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, pk):
        print('aAHHHHHHHHHHHHHHHHHHHHHh')
        event = get_object_or_404(Event, slug=event_slug)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'
            
        bagan = get_object_or_404(Bagan, id_bagan=pk)
        detail_bagan = bagan.id_detailbagan.order_by('-id_score__id_totalscore__total')

        detail_bagan_ids = [detail_bagan for detail_bagan in detail_bagan]

        detail_medali_list = DetailMedali.objects.filter(id_detailbagan__in=detail_bagan_ids)

        midpoint = len(detail_medali_list) // 2

        pairs_list = []

        for i in range(0, len(detail_medali_list), 2):
            if i + 1 < len(detail_medali_list):
                pairs_list.append((detail_medali_list[i], detail_medali_list[i + 1]))
            else:
                pairs_list.append((detail_medali_list[i], None))

        distinct_groups = detail_bagan.values('group_tanding').annotate(group_count=Count('group_tanding')).count()

        middle_group = distinct_groups // 2

        set1 = list(range(1, middle_group + 1))
        set2 = list(range(middle_group + 1, distinct_groups + 1))

        grouped_data = defaultdict(list)
        
        for item in detail_bagan:
            grouped_data[item.group_tanding].append(item)

        grouped_data_list = OrderedDict(sorted(grouped_data.items()))

        group_value = int(distinct_groups)
        group_values = list(range(1, group_value + 1))

        try:
            admintatami = Tatami.objects.get(admin__id_user=request.user)

        except ObjectDoesNotExist:
            admintatami = None
            messages.error(request, "Akun ini tidak memiliki tatami.")
                
        atlet_list = []
        for detail in detail_bagan:
            atlet_list.extend(detail.id_atlet.all())
        
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)

        round_1 = bagan.id_detailbagan.filter(perebutanjuara=5).order_by('group_tanding')
        round_2 = bagan.id_detailbagan.filter(perebutanjuara=4).order_by('group_tanding')
        round_3 = bagan.id_detailbagan.filter(perebutanjuara=3).order_by('group_tanding')
        round_4 = bagan.id_detailbagan.filter(perebutanjuara=2).order_by('group_tanding')
        round_5 = bagan.id_detailbagan.filter(perebutanjuara=1).order_by('group_tanding').first()

        print(round_3)
        print(round_4)

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'bagan': bagan,
            'detail_bagan': detail_bagan,
            'kategori': kategori,
            'atlet_list': atlet_list,
            'admintatami' : admintatami,
            'group_value': group_value,
            'group_values': group_values,
            'grouped_data': grouped_data_list,
            'set1': set1,
            'set2': set2,
            # 'matchup_list': matchup_list,
            'detail_bagan_ids': detail_bagan_ids,
            'detail_medali_list': detail_medali_list,
            'pairs_list': pairs_list,
            # 'first_half_list': first_half_list,
            # 'second_half_list': second_half_list,
            'tatami': tatami,
            'round_1': round_1,
            'round_2': round_2,
            'round_3': round_3,
            'round_4': round_4,
            'round_5': round_5,
        }
        return render(request, 'event/detailbagan.html', context)
    
class DetailBagan(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk):
        event = get_object_or_404(Event, slug=event_slug)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
        bagan = get_object_or_404(Bagan, id_bagan=bagan_pk)
        detail_bagan = bagan.id_detailbagan.filter(bagan=bagan)
        tatami = event.id_tatami.all()
        
        atlet_list = []
        for detail in detail_bagan:
            atlet_list.extend(detail.id_atlet.all())
        
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        
        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'bagan': bagan,
            'detail_bagan': detail_bagan,
            'kategori': kategori,
            'atlet_list': atlet_list,
            'tatami': tatami,
        }
        return render(request, 'event/viewdetailbagan.html', context)
    
class JuryPanel1(View):
    def get(self, request, event_slug, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        tatami = event.id_tatami.get(pk=tatami_pk)

        try:
            detailbagan = DetailBagann.objects.get(id_tatami=tatami)
            related_bagan = detailbagan.bagan_set.first()
            bagan = Bagan.objects.filter(judul_bagan = related_bagan).first()

            if detailbagan.id_score.exists():
                score = detailbagan.id_score.first()
                scoredetail_count = ScoreDetail.objects.filter(id_jury__id_user=request.user, score=score).count()  
                scoredetail1 = ScoreDetail.objects.filter(id_jury__id_user=request.user, score=score, number='1')
                scoredetail2 = ScoreDetail.objects.filter(id_jury__id_user=request.user, score=score, number='2')
            else:
                scoredetail_count = 0

        except DetailBagann.DoesNotExist:
            detailbagan = None
            scoredetail_count = 0
            bagan = 'none'

        scored = 'none'

        if scoredetail_count == 1 and scoredetail1:
            scored = 'scored1'
        
        if scoredetail_count == 1 and scoredetail2:
            scored = 'scored2'

        if scoredetail_count == 2:
            scored = 'scored3'

        if scoredetail_count == 0:
            scored = 'none'
        
        group = 'none'

        try:
            detailbagan = DetailBagann.objects.get(id_tatami=tatami)
            atlet_count = detailbagan.id_atlet.count()
            
            if atlet_count == 2:
                atlet1a = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=1).first()
                atlet1 = atlet1a.id_atlet
                atlet2a = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=2).first()
                atlet2 = atlet2a.id_atlet
            else:
                atlet1 = detailbagan.id_atlet.first()
                atlet2 = detailbagan.id_atlet.last()

            if detailbagan.peserta1:
                group = 'merah'

            elif detailbagan.peserta2:
                group = 'biru'

        except ObjectDoesNotExist:
            # Perform your desired action here
            detailbagan = None
            atlet1 = None
            atlet2 = None
            group = 'none'
            
        jury = request.user.jury
        jury_number = jury.number

        context = {
            'event': event,
            'tatami': tatami,
            'detailbagan': detailbagan,
            'atlet1': atlet1,
            'atlet2': atlet2,
            'group': group,
            'scored': scored,
            'bagan': bagan,
        }
        return render(request, 'event/jury.html', context)
    
class JuryPanel2(View):
    def get(self, request, event_slug, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        tatami = event.id_tatami.get(pk=tatami_pk)
        
        try:
            detailbagan = DetailBagann.objects.get(id_tatami=tatami)
            atlet1 = detailbagan.id_atlet.first()
            atlet2 = detailbagan.id_atlet.last()
        except ObjectDoesNotExist:
            # Perform your desired action here
            detailbagan = None
            atlet1 = None
            atlet2 = None
            
        jury = request.user.jury
        jury_number = jury.number

        group = 'biru'
        
        context = {
            'event': event,
            'tatami': tatami,
            'detailbagan': detailbagan,
            'atlet1': atlet1,
            'atlet2': atlet2,
            'group': group,
        }
        return render(request, 'event/jury.html', context)
    
from asgiref.sync import async_to_sync
def jurysendbendera(request, event_slug, tatami_pk):
    channel_layer = get_channel_layer()
    event = get_object_or_404(Event, slug=event_slug)
    tatami = event.id_tatami.get(pk=tatami_pk)

    try:
        detailbagan = DetailBagann.objects.get(id_tatami=tatami)
        room_name = f'ring_{tatami_pk}_{detailbagan.pk}'
    except DetailBagann.DoesNotExist:
        detailbagan = None

    if detailbagan.id_score.exists():
        score = detailbagan.id_score.first()
    else:
        score = Score.objects.create()
        detailbagan.id_score.add(score)

    related_bagan = detailbagan.bagan_set.first()
    bagan = Bagan.objects.get(judul_bagan = related_bagan)

    jury = request.user.jury
    jury_number = jury.number

    bendera = request.POST.get('bendera')

    scoredetail_count = ScoreDetail.objects.filter(id_jury__id_user=request.user, score=score).count()  
    

    if bendera == 'merah':
        input1 = 20
    else:
        input1 = 30

    if scoredetail_count > 0:
        # Update existing ScoreDetail object
        try:
            scoredetail1 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=1)
            scoredetail1.jury_score = input1
            scoredetail1.save()
            score.juri_score.add(scoredetail1)
            detailbagan.id_scoredetail.add(scoredetail1)
        except ObjectDoesNotExist:
            # Create a new ScoreDetail object
            scoredetail1 = ScoreDetail.objects.create(jury_score=input1)
            scoredetail1.id_jury.add(jury)
            scoredetail1.nama = f"Jury {jury_number}"
            scoredetail1.number = f'1'
            scoredetail1.save()
            score.juri_score.add(scoredetail1)
            detailbagan.id_scoredetail.add(scoredetail1)
    else:
        scoredetail1 = ScoreDetail.objects.create(jury_score=input1)
        scoredetail1.id_jury.add(jury)
        scoredetail1.nama = f"Jury {jury_number}"
        scoredetail1.number = f'1'
        scoredetail1.save()
        score.juri_score.add(scoredetail1)
        detailbagan.id_scoredetail.add(scoredetail1)

        score_count1 = detailbagan.id_scoredetail.filter(number=1).count()

    if bagan.banyaknya_juri == 5:
        if score_count1 == 5:
            valid = 'yes'
        else:
            valid = 'no'
    elif bagan.banyaknya_juri == 3:
        if score_count1 == 3:
            valid = 'yes'
        else:
            valid = 'no'
    elif bagan.banyaknya_juri == 7:
        if score_count1 == 7:
            valid = 'yes'
        else:
            valid = 'no'

    input2 = 0

    async_to_sync(channel_layer.group_send)(
        f"{room_name}", 
        {
            'type': 'sendscore',
            'sender': jury_number,
            'message1': input1,
            'message2': input2,
            'valid': valid,
        }
    )    

    return redirect('jurypanel1', event_slug, tatami_pk)

def jurysendscore(request, event_slug, tatami_pk):    
    channel_layer = get_channel_layer()
    event = get_object_or_404(Event, slug=event_slug)
    tatami = event.id_tatami.get(pk=tatami_pk)
        
    try:
        detailbagan = DetailBagann.objects.get(id_tatami=tatami)
        room_name = f'ring_{tatami_pk}_{detailbagan.pk}'
    except DetailBagann.DoesNotExist:
        detailbagan = None
    
    if detailbagan.id_score.exists():
        score = detailbagan.id_score.first()
    else:
        score = Score.objects.create()
        detailbagan.id_score.add(score)

    related_bagan = detailbagan.bagan_set.first()
    bagan = Bagan.objects.get(judul_bagan = related_bagan)
    
    jury = request.user.jury
    jury_number = jury.number
    
    input1 = request.POST.get('input1')
    input2 = request.POST.get('input2')

    submit_button = request.POST.get('submit_button')

    if submit_button == 'diskualifikasi1':
        input1 = 0

    if submit_button == 'diskualifikasi2':
        input2 = 0
    
    # # Get the count of existing ScoreDetail objects associated with the current user's Jury
    scoredetail_count = ScoreDetail.objects.filter(id_jury__id_user=request.user, score=score).count()  
        
    if detailbagan.id_atlet.count() == 2:
        atlet1 = detailbagan.id_atlet.first()
        atlet2 = detailbagan.id_atlet.last()
        if detailbagan.peserta1:
            if scoredetail_count > 0:
                # Update existing ScoreDetail object
                try:
                    scoredetail1 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=1)
                    scoredetail1.jury_score = input1
                    atlet1.id_score.add(scoredetail1)
                    atlet1.save()
                    scoredetail1.save()
                    score.juri_score.add(scoredetail1)
                    detailbagan.id_scoredetail.add(scoredetail1)
                except ObjectDoesNotExist:
                    # Create a new ScoreDetail object
                    scoredetail1 = ScoreDetail.objects.create(jury_score=input1)
                    scoredetail1.id_jury.add(jury)
                    scoredetail1.nama = f"Jury {jury_number}"
                    scoredetail1.number = f'1'
                    scoredetail1.save()
                    atlet1.id_score.add(scoredetail1)
                    atlet1.save()
                    score.juri_score.add(scoredetail1)
                    detailbagan.id_scoredetail.add(scoredetail1)
            else:
                scoredetail1 = ScoreDetail.objects.create(jury_score=input1)
                scoredetail1.id_jury.add(jury)
                scoredetail1.nama = f"Jury {jury_number}"
                scoredetail1.number = f'1'
                scoredetail1.save()
                atlet1.id_score.add(scoredetail1)
                atlet1.save()
                score.juri_score.add(scoredetail1)
                detailbagan.id_scoredetail.add(scoredetail1)

            score_count1 = detailbagan.id_scoredetail.filter(number=1).count()

            if bagan.banyaknya_juri == 5:
                if score_count1 == 5:
                    valid = 'yes'
                else:
                    valid = 'no'
            elif bagan.banyaknya_juri == 3:
                if score_count1 == 3:
                    valid = 'yes'
                else:
                    valid = 'no'
            elif bagan.banyaknya_juri == 7:
                if score_count1 == 7:
                    valid = 'yes'
                else:
                    valid = 'no'
            
        elif detailbagan.peserta2:
            if scoredetail_count > 0:
                try:
                    scoredetail2 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=2)
                    scoredetail2.jury_score = input2
                    atlet2.id_score.add(scoredetail2)
                    atlet2.save()
                    scoredetail2.save()
                    score.juri_score.add(scoredetail2)
                    detailbagan.id_scoredetail.add(scoredetail2)
                except ObjectDoesNotExist:
                    # Create a new ScoreDetail object
                    scoredetail2 = ScoreDetail.objects.create(jury_score=input2)
                    scoredetail2.id_jury.add(jury)
                    scoredetail2.nama = f"Jury {jury_number}"
                    scoredetail2.number = f'2'
                    scoredetail2.save()
                    atlet2.id_score.add(scoredetail2)
                    atlet2.save()
                    score.juri_score.add(scoredetail2)
                    detailbagan.id_scoredetail.add(scoredetail2)
            else:    
                scoredetail2 = ScoreDetail.objects.create(jury_score=input2)
                scoredetail2.id_jury.add(jury)
                scoredetail2.nama = f"Jury {jury_number}"
                scoredetail2.number = f'2'
                scoredetail2.save()
                atlet2.id_score.add(scoredetail2)
                atlet2.save()
                score.juri_score.add(scoredetail2)
                detailbagan.id_scoredetail.add(scoredetail2)
            
            score_count2 = detailbagan.id_scoredetail.filter(number=2).count()

            if bagan.banyaknya_juri == 5:
                if score_count2 == 5:
                    valid = 'yes'
                else:
                    valid = 'no'
            elif bagan.banyaknya_juri == 3:
                if score_count2 == 3:
                    valid = 'yes'
                else:
                    valid = 'no'
            elif bagan.banyaknya_juri == 7:
                if score_count2 == 7:
                    valid = 'yes'
                else:
                    valid = 'no'
            
        if detailbagan.peserta1:
            try:
                scoredetail2 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=2)
                input2a = scoredetail2
                input2_serialized = serializers.serialize('json', [input2a])
                input2_data = json.loads(input2_serialized)
                input2 = input2_data[0]['fields']['jury_score']
            except ObjectDoesNotExist:
                scoredetail2 = '0.0'
                input2 = scoredetail2

        elif detailbagan.peserta2:
            try:
                scoredetail1 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=1)
                input1a = scoredetail1
                input1_serialized = serializers.serialize('json', [input1a])
                input1_data = json.loads(input1_serialized)
                input1 = input1_data[0]['fields']['jury_score']
            except ObjectDoesNotExist:
                scoredetail1 = '0.0'
                input1 = scoredetail1 

        async_to_sync(channel_layer.group_send)(
            f"{room_name}", 
            {
                'type': 'sendscore',
                'sender': jury_number,
                'message1': input1,
                'message2': input2,
                'valid': valid,
            }
        )  

        return redirect('jurypanel1', event_slug, tatami_pk)
    
    else:
        atlet1 = detailbagan.id_atlet.first()
        
        if detailbagan.peserta1:
            if scoredetail_count > 0:
                try:
                    scoredetail1 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=1)
                    scoredetail1.jury_score = input1
                    atlet1.id_score.add(scoredetail1)
                    atlet1.save()
                    scoredetail1.save()
                    score.juri_score.add(scoredetail1)
                    detailbagan.id_scoredetail.add(scoredetail1)
                except ObjectDoesNotExist:
                    scoredetail1 = ScoreDetail.objects.create(jury_score=input1)
                    scoredetail1.id_jury.add(jury)
                    scoredetail1.nama = f"Jury {jury_number}"
                    scoredetail1.number = f'1'
                    scoredetail1.save()
                    atlet1.id_score.add(scoredetail1)
                    atlet1.save()
                    score.juri_score.add(scoredetail1)
                    detailbagan.id_scoredetail.add(scoredetail1)
            else:
                scoredetail1 = ScoreDetail.objects.create(jury_score=input1)
                scoredetail1.id_jury.add(jury)
                scoredetail1.nama = f"Jury {jury_number}"
                scoredetail1.number = f'1'
                scoredetail1.save()
                atlet1.id_score.add(scoredetail1)
                atlet1.save()
                score.juri_score.add(scoredetail1)
                detailbagan.id_scoredetail.add(scoredetail1)
        
            score.juri_score.add(scoredetail1)
            detailbagan.id_scoredetail.add(scoredetail1)
            score_count = detailbagan.id_scoredetail.count()
            
        else:
            if scoredetail_count > 0:
                try:
                    scoredetail2 = ScoreDetail.objects.get(id_jury__id_user=request.user, score=score, number=2)
                    scoredetail2.jury_score = input2
                    atlet1.id_score.add(scoredetail2)
                    atlet1.save()
                    scoredetail2.save()
                    score.juri_score.add(scoredetail2)
                    detailbagan.id_scoredetail.add(scoredetail2)
                except ObjectDoesNotExist:
                    scoredetail2 = ScoreDetail.objects.create(jury_score=input2)
                    scoredetail2.id_jury.add(jury)
                    scoredetail2.nama = f"Jury {jury_number}"
                    scoredetail2.number = f'2'
                    scoredetail2.save()
                    atlet1.id_score.add(scoredetail2)
                    atlet1.save()
                    score.juri_score.add(scoredetail2)
                    detailbagan.id_scoredetail.add(scoredetail2)
            else:
                scoredetail2 = ScoreDetail.objects.create(jury_score=input2)
                scoredetail2.id_jury.add(jury)
                scoredetail2.nama = f"Jury {jury_number}"
                scoredetail2.number = f'2'
                scoredetail2.save()
                atlet1.id_score.add(scoredetail2)
                atlet1.save()
                score.juri_score.add(scoredetail2)
                detailbagan.id_scoredetail.add(scoredetail2)
        
            score.juri_score.add(scoredetail2)
            detailbagan.id_scoredetail.add(scoredetail2)
            score_count = detailbagan.id_scoredetail.count()

        if bagan.banyaknya_juri == 5:
            if score_count == 5:
                valid = 'yes'
            else:
                valid = 'no'
        elif bagan.banyaknya_juri == 3:
            if score_count == 3:
                valid = 'yes'
            else:
                valid = 'no'
        elif bagan.banyaknya_juri == 7:
            if score_count == 7:
                valid = 'yes'
            else:
                valid = 'no'
        
        print(bagan.banyaknya_juri)
        print(score_count)
        

        async_to_sync(channel_layer.group_send)(
                f"{room_name}", 
                {
                    'type': 'sendscore',
                    'sender': jury_number,
                    'message1': input1,
                    'message2': input2,
                    'valid': valid,
                }
            )    
        return redirect('jurypanel1', event_slug, tatami_pk)

class controlPanel1(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()

        
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        # detailbagan = DetailBagann.objects.filter(pk=detailbagan_pk, bagan=bagan).first()
        tatami = get_object_or_404(Tatami, pk=tatami_pk)
        atlet = detailbagan.id_atlet.all()
        
        juri1 = tatami.id_jury.get(number=1)
        juri2 = tatami.id_jury.get(number=2)
        juri3 = tatami.id_jury.get(number=3)
        juri4 = tatami.id_jury.get(number=4)
        juri5 = tatami.id_jury.get(number=5)
        juri6 = tatami.id_jury.get(number=6)
        juri7 = tatami.id_jury.get(number=7)
    
        score = detailbagan.id_score.first()
        
        if score is not None:
            score1 = score.juri_score.filter(number=1)
            score2 = score.juri_score.filter(number=2)
        
            score1j1 = score1.filter(number=1, id_jury=juri1).first()
            score1j2 = score1.filter(number=1, id_jury=juri2).first()
            score1j3 = score1.filter(number=1, id_jury=juri3).first()
            score1j4 = score1.filter(number=1, id_jury=juri4).first()
            score1j5 = score1.filter(number=1, id_jury=juri5).first()
            score1j6 = score1.filter(number=1, id_jury=juri6).first()
            score1j7 = score1.filter(number=1, id_jury=juri7).first()
            
            score2j1 = score2.filter(number=2, id_jury=juri1).first()
            score2j2 = score2.filter(number=2, id_jury=juri2).first()
            score2j3 = score2.filter(number=2, id_jury=juri3).first()
            score2j4 = score2.filter(number=2, id_jury=juri4).first()
            score2j5 = score2.filter(number=2, id_jury=juri5).first()
            score2j6 = score2.filter(number=2, id_jury=juri6).first()
            score2j7 = score2.filter(number=2, id_jury=juri7).first()

            try:
                totalscore = score.id_totalscore.filter(number=1).first()
            except ObjectDoesNotExist:
                totalscore = "00.0"

            try:
                totalscore1 = score.id_totalscore.filter(number=2).first()
            except ObjectDoesNotExist:
                totalscore1 = "00.0"

        else:
            score1j1 = 'Belum Dikirim'
            score1j2 = 'Belum Dikirim'
            score1j3 = 'Belum Dikirim'
            score1j4 = 'Belum Dikirim'
            score1j5 = 'Belum Dikirim'
            score1j6 = 'Belum Dikirim'
            score1j7 = 'Belum Dikirim'
            
            score2j1 = 'Belum Dikirim'
            score2j2 = 'Belum Dikirim'
            score2j3 = 'Belum Dikirim'
            score2j4 = 'Belum Dikirim'
            score2j5 = 'Belum Dikirim'
            score2j6 = 'Belum Dikirim'
            score2j7 = 'Belum Dikirim'

            totalscore = "00.0"
            totalscore1 = "00.0"

        try:
            # Try to get a DetailBagann instance with the current tatami
            existing_detailbagan = DetailBagann.objects.get(id_tatami=tatami)
            existing_detailbagan.id_tatami = None  # Remove the existing relationship
            existing_detailbagan.save()
        except ObjectDoesNotExist:
            pass  # No existing relationship, do nothing

        detailbagan.penilaian = True
        detailbagan.id_tatami = tatami
        detailbagan.save()
        
        url = reverse('controlpanel1', kwargs={
            'event_slug': event.slug,
            'kategori_slug': kategori.slug,
            'jenis_kelamin': jenis_kelamin,
            'bagan_pk': bagan.pk,
            'detailbagan_pk': detailbagan.pk,
            'tatami_pk': tatami_pk,
        })
        
        url_parts = request.path.split('/')
        internal = 'internal' in url_parts
        external = 'external' in url_parts
        
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})

        detail_bagan = bagan.id_detailbagan.order_by('-id_score__id_totalscore__total')
        atlet_count = detailbagan.id_atlet.count()
        distinct_groups = detail_bagan.values('group_tanding').annotate(group_count=Count('group_tanding')).count()
        group1 = 'none'
        group2 = 'none'

        atlet1 = detailbagan.id_atlet.first()
        atlet2 = detailbagan.id_atlet.last()
        
        if atlet_count == 1:
            middle_group = distinct_groups // 2
            set1 = list(range(1, middle_group + 1))
            set2 = list(range(middle_group + 1, distinct_groups + 1))

            if detailbagan.group_tanding in set1:
                group1 = 'merah'
            elif detailbagan.group_tanding in set2:
                group1 = 'biru'
            
        elif atlet_count == 2:
            atlet1 = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=1).first()
            atlet2 = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=2).first()

            group1 = 'merah'
            group2 = 'biru'

        bendera = 'none'
        winner = 'none'

        if bagan.banyaknya_juri == 3:
            if detailbagan.id_scoredetail.count() == 3:
                bendera = 'full'
        elif bagan.banyaknya_juri == 5:
            if detailbagan.id_scoredetail.count() == 5:
                bendera = 'full'
        elif bagan.banyaknya_juri == 7:
            if detailbagan.id_scoredetail.count() == 7:
                bendera = 'full'
            
        if bendera == 'full':
            merah = detailbagan.id_scoredetail.filter(jury_score = 20).count()
            biru = detailbagan.id_scoredetail.filter(jury_score = 30).count()

            if merah > biru:
                winner = 'merah'
            elif biru > merah:
                winner = 'biru'

        try:
            DetailMedali.objects.get(id_detailbagan=detailbagan, number=1)
        except ObjectDoesNotExist:
            DetailMedali.objects.create(id_detailbagan=detailbagan, number=1, id_atlet=detailbagan.atlet1, nama=f'{detailbagan.atlet1}')

        try:
            DetailMedali.objects.get(id_detailbagan=detailbagan, number=2)
        except ObjectDoesNotExist:
            DetailMedali.objects.create(id_detailbagan=detailbagan, number=2, id_atlet=detailbagan.atlet2, nama=f'{detailbagan.atlet2}')


        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'detailbagan': detailbagan,
            'detail_bagan': detail_bagan,
            'kategori': kategori,
            'controlpanel1_url': url, 
            'internal': internal,
            'external': external,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
            'tatami': tatami,
            'atlet': atlet,
            'score1j1': score1j1,
            'score1j2': score1j2,
            'score1j3': score1j3,
            'score1j4': score1j4,
            'score1j5': score1j5,
            'score1j6': score1j6,
            'score1j7': score1j7,
            'score2j1': score2j1,
            'score2j2': score2j2,
            'score2j3': score2j3,
            'score2j4': score2j4,
            'score2j5': score2j5,
            'score2j6': score2j6,
            'score2j7': score2j7,
            'atlet1': atlet1,
            'atlet2': atlet2,
            'totalscore1': totalscore,
            'totalscore2': totalscore1,
            'group1': group1,
            'group2': group2,
            'atlet_count': atlet_count,
            'penilaian_juri': bagan.banyaknya_juri,
            'tatami': tatami,
            'bendera': bendera,
            'winner': winner,
        }
        
        return render(request, 'event/controlpanel1.html', context)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        form_type = request.POST.get('submit_button')
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk)
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detail_bagan = bagan.id_detailbagan.order_by('-id_score__id_totalscore__total')
        atlet_count = detailbagan.id_atlet.count()

        if form_type == 'submit_kata':
            input_kata = request.POST.get('input_kata')
            if atlet_count == 1:
                distinct_groups = detail_bagan.values('group_tanding').annotate(group_count=Count('group_tanding')).count()
                middle_group = distinct_groups // 2
                set1 = list(range(1, middle_group + 1))
                set2 = list(range(middle_group + 1, distinct_groups + 1))

                if detailbagan.group_tanding in set1: ## Merah
                    detailbagan.kata1 = input_kata
                elif detailbagan.group_tanding in set2: ## Biru
                    detailbagan.kata2 = input_kata

                detailbagan.save()
            if atlet_count == 2:
                input_kata = request.POST.get('input_kata')
                warna = request.POST.get('warna')
                if warna == 'aka':
                    detailbagan.kata1 = input_kata
                elif warna == 'ao':
                    detailbagan.kata2 = input_kata
                else:
                    print('TIDAK ADAAAA')
                detailbagan.save()
        
        if form_type == 'penilaian_ulang1':
            detailbagan_pk = request.POST.get('detailbagan1')
            detailbagan_obj = DetailBagann.objects.get(pk=detailbagan_pk)
            score = detailbagan_obj.id_score.first()
            detail_bagan = bagan.id_detailbagan.order_by('-id_score__id_totalscore__total')
            atlet_count = detailbagan_obj.id_atlet.count()
            try:
                total_scores = score.id_totalscore.all()
            except AttributeError:
                total_scores = ""

            distinct_groups = detail_bagan.values('group_tanding').annotate(group_count=Count('group_tanding')).count()
            middle_group = distinct_groups // 2
            set1 = list(range(1, middle_group + 1))
            set2 = list(range(middle_group + 1, distinct_groups + 1))

            if detailbagan_obj.dinilai == True:
                detailbagan_obj.dinilai = False
                detailbagan_obj.penilaian = True

            if atlet_count == 1: 
                try:
                    score_details = score.juri_score.all()
                except AttributeError:
                    score_details = ""

                for score_detail in score_details:
                    score_detail.delete()

                for total_score in total_scores:
                    total_score.delete() 

                if detailbagan_obj.group_tanding in set1: ## Merah
                    detailbagan_obj.peserta1 = True
                    detailbagan_obj.peserta1_telahdinilai = False     

                elif detailbagan_obj.group_tanding in set2: ## Biru
                    detailbagan_obj.peserta2 = True
                    detailbagan_obj.peserta2_telahdinilai = False

                detailbagan_obj.save()

            else: ## Jika atletnya 2
                detailbagan_obj.peserta1 = True
                detailbagan_obj.peserta1_telahdinilai = False

                if detailbagan_obj.peserta2 == True:
                    detailbagan_obj.peserta2 = False

                try:
                    score_details = score.juri_score.filter(number=1)
                except AttributeError:
                    score_details = ""
                try:
                    total_scores = score.id_totalscore.filter(number=1)
                except AttributeError:
                    total_score = ""
                    

                for score_detail in score_details:
                    score_detail.delete()
                for totalscore in total_scores:
                    totalscore.delete()

                detailbagan_obj.save()
        
        else:
            if form_type == 'penilaian_ulang1':
                detailbagan_pk = request.POST.get('detailbagan1')
                detailbagan_obj = DetailBagann.objects.get(pk=detailbagan_pk)
                score = detailbagan_obj.id_score.first()
                total_scores = score.id_totalscore.all()
                detailbagan_obj.peserta1 = True
                detailbagan_obj.peserta1_telahdinilai = False
                if detailbagan_obj.peserta2 == True:
                    detailbagan_obj.peserta2 = False
                score_details = score.juri_score.filter(number=1)
                total_scores = score.id_totalscore.filter(number=1)
                for score_detail in score_details:
                    score_detail.delete()
                for totalscore in total_scores:
                    totalscore.delete()
                detailbagan_obj.save()
            if form_type == 'penilaian_ulang2':
                detailbagan_pk = request.POST.get('detailbagan2')
                detailbagan_obj = DetailBagann.objects.get(pk=detailbagan_pk)
                score = detailbagan_obj.id_score.first()
                try:
                    total_scores = score.id_totalscore.all()
                except AttributeError:
                    total_scores = ""
                detailbagan_obj.peserta2 = True
                detailbagan_obj.peserta2_telahdinilai = False
                if detailbagan_obj.peserta1 == True:
                    detailbagan_obj.peserta1 = False
                try:
                    score_details = score.juri_score.filter(number=2)
                except AttributeError:
                    score_details = ""
                try:
                    total_scores = score.id_totalscore.filter(number=2)
                except AttributeError:
                    total_scores = ""

                for score_detail in score_details:
                    score_detail.delete()
                for totalscore in total_scores:
                    totalscore.delete()
                detailbagan_obj.save()

        return redirect('controlpanel1', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, bagan_pk=bagan_pk, detailbagan_pk=detailbagan_pk, tatami_pk=tatami_pk)
    
class LihatScore(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        tatami = get_object_or_404(Tatami, pk=tatami_pk)
        atlet = detailbagan.id_atlet.all()

        atlet_count = detailbagan.id_atlet.count()

        group1 = 'none'
        group2 = 'none'

        if atlet_count == 2:
            atlet1a = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=1).first()
            atlet1 = atlet1a.id_atlet
            atlet2a = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=2).first()
            atlet2 = atlet2a.id_atlet
        else:
            detail_bagan = bagan.id_detailbagan.order_by('-id_score__id_totalscore__total')
            distinct_groups = detail_bagan.values('group_tanding').annotate(group_count=Count('group_tanding')).count()
            
            middle_group = distinct_groups // 2
            set1 = list(range(1, middle_group + 1))
            set2 = list(range(middle_group + 1, distinct_groups + 1))

            if detailbagan.group_tanding in set1:
                group1 = 'merah'
            elif detailbagan.group_tanding in set2:
                group1 = 'biru'

            atlet1 = detailbagan.id_atlet.first()
            atlet2 = detailbagan.id_atlet.last()
        
        
        juri1 = tatami.id_jury.get(number=1)
        juri2 = tatami.id_jury.get(number=2)
        juri3 = tatami.id_jury.get(number=3)
        juri4 = tatami.id_jury.get(number=4)
        juri5 = tatami.id_jury.get(number=5)
        juri6 = tatami.id_jury.get(number=6)
        juri7 = tatami.id_jury.get(number=7)
        
        score = detailbagan.id_score.first()
        
        if score is not None:
            score1 = score.juri_score.filter(number=1)
            score2 = score.juri_score.filter(number=2)
        
            score1j1 = score1.filter(number=1, id_jury=juri1).first()
            score1j2 = score1.filter(number=1, id_jury=juri2).first()
            score1j3 = score1.filter(number=1, id_jury=juri3).first()
            score1j4 = score1.filter(number=1, id_jury=juri4).first()
            score1j5 = score1.filter(number=1, id_jury=juri5).first()
            score1j6 = score1.filter(number=1, id_jury=juri6).first()
            score1j7 = score1.filter(number=1, id_jury=juri7).first()
            
            score2j1 = score2.filter(number=2, id_jury=juri1).first()
            score2j2 = score2.filter(number=2, id_jury=juri2).first()
            score2j3 = score2.filter(number=2, id_jury=juri3).first()
            score2j4 = score2.filter(number=2, id_jury=juri4).first()
            score2j5 = score2.filter(number=2, id_jury=juri5).first()
            score2j6 = score2.filter(number=2, id_jury=juri6).first()
            score2j7 = score2.filter(number=2, id_jury=juri7).first()

            totalscore = score.id_totalscore.filter(number=1).first()
            totalscore1 = score.id_totalscore.filter(number=2).first()
            # totalscore = score.id_totalscore.first()
            # totalscore1 = score.id_totalscore.last()

        else:
            score1j1 = 'Belum Dikirim'
            score1j2 = 'Belum Dikirim'
            score1j3 = 'Belum Dikirim'
            score1j4 = 'Belum Dikirim'
            score1j5 = 'Belum Dikirim'
            score1j6 = 'Belum Dikirim'
            score1j7 = 'Belum Dikirim'
            
            score2j1 = 'Belum Dikirim'
            score2j2 = 'Belum Dikirim'
            score2j3 = 'Belum Dikirim'
            score2j4 = 'Belum Dikirim'
            score2j5 = 'Belum Dikirim'
            score2j6 = 'Belum Dikirim'
            score2j7 = 'Belum Dikirim'

            totalscore = "00.00"
            totalscore1 = "00.00"

        try:
            # Try to get a DetailBagann instance with the current tatami
            existing_detailbagan = DetailBagann.objects.get(id_tatami=tatami)
            existing_detailbagan.id_tatami = None  # Remove the existing relationship
            existing_detailbagan.save()
        except ObjectDoesNotExist:
            pass  # No existing relationship, do nothing

        detailbagan.penilaian = True
        detailbagan.id_tatami = tatami
        detailbagan.save()
        
        url = reverse('controlpanel1', kwargs={
            'event_slug': event.slug,
            'kategori_slug': kategori.slug,
            'jenis_kelamin': jenis_kelamin,
            'bagan_pk': bagan.pk,
            'detailbagan_pk': detailbagan.pk,
            'tatami_pk': tatami_pk,
        })
        
        url_parts = request.path.split('/')
        internal = 'internal' in url_parts
        external = 'external' in url_parts
        
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})

        merah = detailbagan.id_scoredetail.filter(jury_score = 20).count()
        biru = detailbagan.id_scoredetail.filter(jury_score = 30).count()

        if merah > biru:
            winner = 'merah'
        else:
            winner = 'biru'
        
        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'detailbagan': detailbagan,
            'kategori': kategori,
            'controlpanel1_url': url, 
            'internal': internal,
            'external': external,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
            'tatami': tatami,
            'atlet': atlet,
            'score1j1': score1j1,
            'score1j2': score1j2,
            'score1j3': score1j3,
            'score1j4': score1j4,
            'score1j5': score1j5,
            'score1j6': score1j6,
            'score1j7': score1j7,
            'score2j1': score2j1,
            'score2j2': score2j2,
            'score2j3': score2j3,
            'score2j4': score2j4,
            'score2j5': score2j5,
            'score2j6': score2j6,
            'score2j7': score2j7,
            'penilaian_juri': bagan.banyaknya_juri,
            'atlet1': atlet1,
            'atlet2': atlet2,
            'totalscore1': totalscore,
            'totalscore2': totalscore1,
            'group1': group1,
            'group2': group2,
            'tatami': tatami,
            'winner': winner,
        }
        
        return render(request, 'event/testing.html', context)
    
class MulaiPenilaian1(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        tatami = get_object_or_404(Tatami, pk=tatami_pk)
        atlet = detailbagan.id_atlet.all()
        atlet1 = detailbagan.id_atlet.first()

        if not detailbagan.peserta1:
            detailbagan.peserta1 = True
            detailbagan.save()
        else:
            detailbagan.peserta1 = False
            detailbagan.peserta1_telahdinilai = True
            detailbagan.save()

        return redirect('controlpanel1', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, bagan_pk=bagan_pk, detailbagan_pk=detailbagan_pk, tatami_pk=tatami_pk)

class MulaiPenilaian2(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        tatami = get_object_or_404(Tatami, pk=tatami_pk)
        atlet = detailbagan.id_atlet.all()
        atlet2 = detailbagan.id_atlet.last()

        if not detailbagan.peserta2:
            detailbagan.peserta2 = True
            detailbagan.save()
        else:
            detailbagan.peserta2 = False
            detailbagan.peserta2_telahdinilai = True
            detailbagan.save()

        return redirect('controlpanel1', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, bagan_pk=bagan_pk, detailbagan_pk=detailbagan_pk, tatami_pk=tatami_pk)

def totalnilai(request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
    event = get_object_or_404(Event, slug=event_slug)
    bagan = get_object_or_404(Bagan, pk=bagan_pk)
    bagan_kategori = event.bagan_kategori.all()
    kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
    detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
    tatami = get_object_or_404(Tatami, pk=tatami_pk)
    atlet = detailbagan.id_atlet.all()
    atlet1 = detailbagan.id_atlet.first()
    atlet2 = detailbagan.id_atlet.last()
    
    juri1 = tatami.id_jury.get(number=1)
    juri2 = tatami.id_jury.get(number=2)
    juri3 = tatami.id_jury.get(number=3)
    juri4 = tatami.id_jury.get(number=4)
    juri5 = tatami.id_jury.get(number=5)
    juri6 = tatami.id_jury.get(number=6)
    juri7 = tatami.id_jury.get(number=7)
    
    score = detailbagan.id_score.first()
    
    if score is not None:
        score1 = score.juri_score.filter(number=1)
        score2 = score.juri_score.filter(number=2)

        if bagan.bendera == True:
            merah = detailbagan.id_scoredetail.filter(jury_score = 20).count()
            biru = detailbagan.id_scoredetail.filter(jury_score = 30).count()
            if merah > biru:
                winner = 'merah'
            else:
                winner = 'biru'

            detailbagan.peserta1 = False
            detailbagan.peserta1_telahdinilai = True
            detailbagan.save()

            data = {
                'winner': winner,
            }

        else:
            if detailbagan.peserta1:
                pk_string = "".join(str(obj.pk) for obj in score1)
                # Score tertinggi
                score_values = [float(obj.jury_score) for obj in score1]
                largest_score_index = score_values.index(max(score_values))
                largest_score_object = score1[largest_score_index]
                largest_score_object.tertinggi = True
                largest_score_object.save()

                # Score terendah
                score_values1 = [float(obj.jury_score) for obj in score1]
                largest_score_index1 = score_values1.index(min(score_values1))
                largest_score_object1 = score1[largest_score_index1]
                largest_score_object1.terendah = True
                largest_score_object1.save()

                score1 = [float(obj.jury_score) for obj in score.juri_score.filter(number=1)]

                largest_score = max(score1)
                smallest_score = min(score1)

                if bagan.banyaknya_juri == 3:
                    additional_number = sum([float(obj.jury_score) for obj in score.juri_score.filter(number=1)])
                    additional_number = round(additional_number, 3)

                elif bagan.banyaknya_juri == 5:
                    # Exclude the first occurrence of the smallest and largest scores
                    additional_number = sum([float(obj.jury_score) for obj in score.juri_score.filter(number=1) if float(obj.jury_score) != largest_score and float(obj.jury_score) != smallest_score])
                    additional_number += (score1.count(smallest_score) - 1) * smallest_score
                    additional_number += (score1.count(largest_score) - 1) * largest_score
                    additional_number = round(additional_number, 3)

                elif bagan.banyaknya_juri == 7:
                    # Exclude the first occurrence of the smallest and largest scores
                    additional_number = sum([float(obj.jury_score) for obj in score.juri_score.filter(number=1) if float(obj.jury_score) != largest_score and float(obj.jury_score) != smallest_score])
                    additional_number += (score1.count(smallest_score) - 1) * smallest_score
                    additional_number += (score1.count(largest_score) - 1) * largest_score
                    additional_number = round(additional_number, 3)
                    print(additional_number)
                

                slug_val = f'{score.pk}-{pk_string}'


                total_score, created = TotalScore.objects.get_or_create(number=1, defaults={'total': additional_number}, slug=slug_val)
                
                if not created:
                    total_score.total = additional_number
                    total_score.save()

                score.id_totalscore.add(total_score)

                totalnilai1 = additional_number

                totalnilai2a = score.id_totalscore.filter(number=2).last()

                if totalnilai2a is not None:
                    totalnilai2_serialized = serializers.serialize('json', [totalnilai2a])
                    totalnilai2_data = json.loads(totalnilai2_serialized)
                    totalnilai2 = totalnilai2_data[0]['fields']['total']
                else:
                    totalnilai2 = '00.0'

                detailbagan.peserta1 = False
                detailbagan.peserta1_telahdinilai = True
                detailbagan.save()

                data = {
                    'totalnilai1': totalnilai1,
                    'totalnilai2': totalnilai2,
                    'winner' : 'none',
                }

            elif detailbagan.peserta2:
                pk_string1 = "".join(str(obj.pk) for obj in score2)

                # Score tertinggi
                score_values2 = [float(obj.jury_score) for obj in score2]
                largest_score_index2 = score_values2.index(max(score_values2))
                largest_score_object2 = score2[largest_score_index2]
                largest_score_object2.tertinggi = True
                largest_score_object2.save()

                # Score terendah
                score_values2 = [float(obj.jury_score) for obj in score2]
                largest_score_index2 = score_values2.index(min(score_values2))
                largest_score_object2 = score2[largest_score_index2]
                largest_score_object2.terendah = True
                largest_score_object2.save()

                score2 = [float(obj.jury_score) for obj in score.juri_score.filter(number=2)]

                largest_score1 = max(score2)
                smallest_score1 = min(score2)
                
                print('ksjdfklsjdkfljsdfdsklfklsfjdslkdf')
                
                if bagan.banyaknya_juri == 3:
                    additional_number1 = sum([float(obj.jury_score) for obj in score.juri_score.filter(number=2)])
                    additional_number1 = round(additional_number1, 3)

                elif bagan.banyaknya_juri == 5:
                    # Exclude the first occurrence of the smallest and largest scores
                    additional_number1 = sum([float(obj.jury_score) for obj in score.juri_score.filter(number=2) if float(obj.jury_score) != largest_score1 and float(obj.jury_score) != smallest_score1])
                    additional_number1 += (score2.count(smallest_score1) - 1) * smallest_score1
                    additional_number1 += (score2.count(largest_score1) - 1) * largest_score1
                    additional_number1 = round(additional_number1, 3)

                elif bagan.banyaknya_juri == 7:
                    # Exclude the first occurrence of the smallest and largest scores
                    additional_number1 = sum([float(obj.jury_score) for obj in score.juri_score.filter(number=2) if float(obj.jury_score) != largest_score1 and float(obj.jury_score) != smallest_score1])
                    additional_number1 += (score2.count(smallest_score1) - 1) * smallest_score1
                    additional_number1 += (score2.count(largest_score1) - 1) * largest_score1
                    additional_number1 = round(additional_number1, 3)
                    print(additional_number1)
                
                slug_val1 = f'{score.pk}-{pk_string1}'
                    
                total_score1, created = TotalScore.objects.get_or_create(number=2, defaults={'total': additional_number1}, slug=slug_val1)
                
                if not created:
                    total_score1.total = additional_number1
                    total_score1.save()

                score.id_totalscore.add(total_score1)

                totalnilai2 = additional_number1

                totalnilai1a = score.id_totalscore.filter(number=1).last()

                if totalnilai1a is not None:
                    totalnilai1_serialized = serializers.serialize('json', [totalnilai1a])
                    totalnilai1_data = json.loads(totalnilai1_serialized)
                    totalnilai1 = totalnilai1_data[0]['fields']['total']
                else:
                    totalnilai1 = '00.0'

                detailbagan.peserta2 = False
                detailbagan.peserta2_telahdinilai = True
                detailbagan.save()

                data = {
                    'totalnilai2': totalnilai2,
                    'totalnilai1': totalnilai1,
                    'winner' : 'none',
                }    

    # return redirect('controlpanel1', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, bagan_pk=bagan_pk, detailbagan_pk=detailbagan_pk, tatami_pk=tatami_pk)
    return JsonResponse(data)
    
class LeaveControlPanel(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        
        detailbagan.penilaian = False
        detailbagan.id_tatami = None
        # detailbagan.dinilai = True
        detailbagan.save()

        if bagan.new == True:
            print('AHHHHHHHHHHHSKDFJDSFJLKSDJFKLDSJFK')
            try:
                score1 = detailbagan.id_score.first().id_totalscore.get(number=1)
                score1 = score1.total
                print(score1)
            except ObjectDoesNotExist:
                score1 = 0
                print(score1)
            try:
                score2 = detailbagan.id_score.first().id_totalscore.get(number=2)
                score2 = score2.total
                print(score2)
            except ObjectDoesNotExist:
                score2 = 0
                print(score2)

            if detailbagan.group_tanding == 1 and detailbagan.perebutanjuara == 5:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif detailbagan.group_tanding == 2 and detailbagan.perebutanjuara == 5:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif detailbagan.group_tanding == 3 and detailbagan.perebutanjuara == 5:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
            
            elif detailbagan.group_tanding == 4 and detailbagan.perebutanjuara == 5:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif detailbagan.group_tanding == 5 and detailbagan.perebutanjuara == 5:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif detailbagan.group_tanding == 6 and detailbagan.perebutanjuara == 5:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
            
            elif detailbagan.group_tanding == 7 and detailbagan.perebutanjuara == 5:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif detailbagan.group_tanding == 8 and detailbagan.perebutanjuara == 5:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            if detailbagan.group_tanding == 1 and detailbagan.perebutanjuara == 4:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
                print("YESSSSSSSSSSSSSSSSSSSSSSS1111")

            elif detailbagan.group_tanding == 2 and detailbagan.perebutanjuara == 4:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif detailbagan.group_tanding == 3 and detailbagan.perebutanjuara == 4:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
            
            elif detailbagan.group_tanding == 4 and detailbagan.perebutanjuara == 4:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            if detailbagan.group_tanding == 1 and detailbagan.perebutanjuara == 3:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                    print("YESSSSSSSSSSSSSSSSSSSSSSS")
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
                print("YESSSSSSSSSSSSSSSSSSSSSSS")

            elif detailbagan.group_tanding == 2 and detailbagan.perebutanjuara == 3:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
                    print("NOOOOOOOOOOOOOOOOOOOOOOOo")
                print("NOOOOOOOOOOOOOOOOOOOOOOOo")
            
            if detailbagan.group_tanding == 1 and detailbagan.perebutanjuara == 2:
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=1)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=1)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()


        return redirect('keldetailbagan', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, pk=bagan_pk)

class StartTimer1(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)

        if not detailbagan.timer_status:
            detailbagan.timer_status = True
            detailbagan.save()

        return JsonResponse({'success': True})

class TimerStatus1(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        # detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        tatami = get_object_or_404(Tatami, pk=tatami_pk)
        
        detailbagan = get_object_or_404(DetailBagann, id_tatami=tatami)
        bagan = detailbagan.bagan_set.all().first()

        related_bagan = detailbagan.bagan_set.first()
        bagan_now = Bagan.objects.get(judul_bagan = related_bagan)

        timer_status = "Running" if detailbagan.timer_status else "Paused"
        timer_reset = "Reset" if detailbagan.timer_reset else "No"
        change = "Change" if detailbagan.grup else "Nay"
        tampilkan_status = "Tampilkan" if detailbagan.tampilkan else "Tidak"

        atlet_count = detailbagan.id_atlet.count()
        
        if atlet_count == 1:
            peserta1_obj = detailbagan.id_atlet.first()
            peserta1 = peserta1_obj.nama_atlet
            peserta1_perwakilan = peserta1_obj.perwakilan
            peserta1_perguruan = peserta1_obj.perguruan
            totalgroups = bagan.id_detailbagan.aggregate(max_number=Max('group_tanding'))['max_number']
            divided = totalgroups // 2

            if detailbagan.group_tanding > divided:
                peserta1_warna = 'biru'
                kata_2 = detailbagan.kata2
                kata_1 = '-'
            else:
                peserta1_warna = 'merah'
                kata_1 = detailbagan.kata1
                kata_2 = '-'
                

            peserta2_dm = '-'
            peserta2_obj = '-'
            peserta2 = '-'
            peserta2_perwakilan = '-'
            peserta2_perguruan = '-'
            peserta2_warna = '-' 

            mode = 'penyisihan'

        elif atlet_count == 2:
            peserta1_dm = DetailMedali.objects.get(id_detailbagan=detailbagan, number=1)
            peserta1_obj = peserta1_dm.id_atlet
            peserta1 = peserta1_obj.nama_atlet
            peserta1_perwakilan = peserta1_obj.perwakilan
            peserta1_perguruan = peserta1_obj.perguruan
            peserta1_warna = 'merah'
            kata_1 = detailbagan.kata1
            peserta2_dm = DetailMedali.objects.get(id_detailbagan=detailbagan, number=2)
            peserta2_obj = peserta2_dm.id_atlet
            peserta2 = peserta2_obj.nama_atlet
            peserta2_perwakilan = peserta2_obj.perwakilan
            peserta2_perguruan = peserta2_obj.perguruan
            peserta2_warna = 'biru'
            kata_2 = detailbagan.kata2

            if bagan_now.bendera == True:
                mode = 'bendera'
            else:
                mode = 'medali'
            
        atlet2 = detailbagan.id_atlet.last()
        
        score = detailbagan.id_score.first()

        atlet_count = detailbagan.id_atlet.count()
        
        if atlet_count == 2:
            if score is not None:
                # current
                atlet1a = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=1).first()
                atlet1 = atlet1a.id_atlet
                atlet2a = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=2).first()
                atlet2 = atlet2a.id_atlet
                try:
                    totalscorea = score.id_totalscore.filter(number=1).first()
                    if totalscorea:
                        totalscore_serialized = serializers.serialize('json', [totalscorea])
                        totalscore_data = json.loads(totalscore_serialized)
                        totalscore = totalscore_data[0]['fields']['total']
                    else:
                        totalscore = "00.0"
                except ObjectDoesNotExist:
                    totalscore = "00.0"
                    
                try:
                    totalscore1a = score.id_totalscore.filter(number=2).first()
                    if totalscore1a:
                        totalscore1_serialized = serializers.serialize('json', [totalscore1a])
                        totalscore1_data = json.loads(totalscore1_serialized)
                        totalscore1 = totalscore1_data[0]['fields']['total']
                    else:
                        totalscore1 = "00.0"
                except ObjectDoesNotExist:
                    totalscore1 = "00.0"    

            else:
                totalscore = "00.0"
                totalscore1 = "00.0"

        else:
            if score is not None:
                print('score adaaa')
                try:
                    totalscorea = score.id_totalscore.filter(number=1).first()
                    if totalscorea:
                        totalscore_serialized = serializers.serialize('json', [totalscorea])
                        totalscore_data = json.loads(totalscore_serialized)
                        totalscore = totalscore_data[0]['fields']['total']
                    else:
                        totalscore = "00.0"
                except ObjectDoesNotExist:
                    totalscore = "00.0"
                    
                try:
                    totalscore1a = score.id_totalscore.filter(number=2).first()
                    if totalscore1a:
                        totalscore1_serialized = serializers.serialize('json', [totalscore1a])
                        totalscore1_data = json.loads(totalscore1_serialized)
                        totalscore1 = totalscore1_data[0]['fields']['total']
                        print(totalscore1)
                    else:
                        totalscore1 = "00.0"
                except ObjectDoesNotExist:
                    totalscore1 = "00.0"    

            else:
                print('score tidak ada')
                totalscore = "00.0"
                totalscore1 = "00.0"

        detailbagan.penilaian = True
        detailbagan.id_tatami = tatami
        detailbagan.save()
        
        data = {
            'timer_status': timer_status,
            'timer_reset': timer_reset,
            'change': change,
            'tampilkan_status': tampilkan_status,
            'totalscore1': totalscore,
            'totalscore2': totalscore1,
            'peserta1_nama': peserta1,  
            'peserta1_warna': peserta1_warna,
            'peserta1_perwakilan': peserta1_perwakilan,
            'peserta1_perguruan': peserta1_perguruan,
            'peserta1_kata': kata_1,
            'peserta2_nama': peserta2,  
            'peserta2_warna': peserta2_warna,
            'peserta2_perwakilan': peserta2_perwakilan,
            'peserta2_perguruan': peserta2_perguruan,
            'peserta2_kata': kata_2,
            'mode': mode,
            'benderamerah': detailbagan.id_scoredetail.filter(jury_score=20).count(),
            'benderabiru': detailbagan.id_scoredetail.filter(jury_score=30).count(),
        }
        return JsonResponse(data)
    
class PauseTimer1(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)

        if detailbagan.timer_status:
            detailbagan.timer_status = False
            detailbagan.save()

        return JsonResponse({'success': True})
    
class ResetTimer1(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)

        if not detailbagan.timer_reset:
            detailbagan.timer_reset = True
            detailbagan.save()
        
        return JsonResponse({'success': True})

class ResetTimer2(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)

        if detailbagan.timer_reset:
            detailbagan.timer_reset = False
            detailbagan.save()
        
        return JsonResponse({'success': True})    
    
class TukarWarna1(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)

        if not detailbagan.grup:
            detailbagan.grup = True
            detailbagan.save()
        elif detailbagan.grup:
            detailbagan.grup = False
            detailbagan.save()
        
        return JsonResponse({'success': True})  

class Tampilkan1(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)

        if not detailbagan.tampilkan:
            detailbagan.tampilkan = True
            detailbagan.save()
        else:
            detailbagan.tampilkan = False
            detailbagan.save()

        return JsonResponse({'success': True})

class scoringBoard1(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        event = get_object_or_404(Event, slug=event_slug)
        bagan = get_object_or_404(Bagan, pk=bagan_pk)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        detailbagan = get_object_or_404(DetailBagann, pk=detailbagan_pk, bagan=bagan)
        tatami = get_object_or_404(Tatami, pk=tatami_pk)
        atlet_count = detailbagan.id_atlet.count()

        if bagan.bendera == True:
            tipe = 'bendera'
        else:
            tipe = 'normal'

        group1 = 'none'
        group2 = 'none'

        if atlet_count == 2:
            atlet1a = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=1).first()
            atlet1 = atlet1a.id_atlet
            atlet2a = DetailMedali.objects.filter(id_detailbagan=detailbagan, number=2).first()
            atlet2 = atlet2a.id_atlet
        else:
            detail_bagan = bagan.id_detailbagan.order_by('-id_score__id_totalscore__total')
            distinct_groups = detail_bagan.values('group_tanding').annotate(group_count=Count('group_tanding')).count()
            
            middle_group = distinct_groups // 2
            set1 = list(range(1, middle_group + 1))
            set2 = list(range(middle_group + 1, distinct_groups + 1))

            if detailbagan.group_tanding in set1:
                group1 = 'merah'
            elif detailbagan.group_tanding in set2:
                group1 = 'biru'

            atlet1 = detailbagan.id_atlet.first()
            atlet2 = detailbagan.id_atlet.last()


        kata1 = detailbagan.kata1
        kata2 = detailbagan.kata2

        url = reverse('scoringboard1', kwargs={
            'event_slug': event.slug,
            'kategori_slug': kategori.slug,
            'jenis_kelamin': jenis_kelamin,
            'bagan_pk': bagan.pk,
            'detailbagan_pk': detailbagan.pk,
            'tatami_pk': tatami_pk,
        })

        url_parts = request.path.split('/')
        internal = 'internal' in url_parts
        external = 'external' in url_parts
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
        
        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'detailbagan': detailbagan,
            'kategori': kategori,
            'scoringboard1_url': url, 
            'internal': internal,
            'external': external,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
            'tatami': tatami,
            'atlet1': atlet1,
            'atlet2': atlet2,
            'kata1': kata1,
            'kata2': kata2,
            'group1': group1,
            'group2': group2,
            'tipe': tipe,
        }
        
        return render(request, 'event/sbkata1.html', context)
    
    def post(self, request, event_slug, kategori_slug, jenis_kelamin, bagan_pk, detailbagan_pk, tatami_pk):
        return redirect('scoringboard1', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin, bagan_pk=bagan_pk, detailbagan_pk=detailbagan_pk, tatami_pk=tatami_pk)

class keldetailKategoriInternal(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        bagan = event.id_bagan.filter(kategori_kata=kategori, jenis_kelamin=jenis_kelamin, jenis_event='internal')
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='internal')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})

        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
        }
        return render(request, 'event/kategorikata.html', context)

class keldetailKategoriExternal(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        print('sdkfjsdlkf')
        event = get_object_or_404(Event, slug=event_slug)
        bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        bagan = event.id_bagan.filter(kategori_kata=kategori, jenis_kelamin=jenis_kelamin, jenis_event='external')
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')
        putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})

        context = {
            'event': event,
            'bagan': bagan,
            'bagan_kategori': bagan_kategori,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'putraexternal_url': putraexternal_url,
            'putriexternal_url': putriexternal_url,
        }
        return render(request, 'event/kategorikata.html', context)

class keltambahBagan(View):
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        event = get_object_or_404(Event, slug=event_slug)
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        atlet_putra = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
        atlet_putri = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')

        # Get the URL for putra external
        putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'kategori': kategori,
            'atlet_putra': atlet_putra,
            'atlet_putri': atlet_putri,
            'putraexternal_url': putraexternal_url,
            'putriexternal_url': putriexternal_url,
        }
        return render(request, 'event/tambahbagan.html', context)

class TambahBaganMedali(View):
    def post(self, request, event_slug, kategori_slug, jenis_kelamin):
        print('testestes')
        tipe = request.POST.get('tipe')
        if tipe == 'medali':
            banyaknya_juri = request.POST.get('juri')
            num_loops1 = [1, 2, 3, 4]
            num_loops2 = [1, 2, 3]
            num_loops3 = [1, 2]
            event = get_object_or_404(Event, slug=event_slug)
            bagan = event.id_bagan.all()
            user = request.user.pk
            admin_tatami = AdminTatami.objects.filter(id_user=user).first()
            
            if admin_tatami:
                tatami = Tatami.objects.get(admin=admin_tatami)
                bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
            else:
                bagan_kategori = event.bagan_kategori.all()
            kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
            atlet_putra_internal = kategori.id_atlet.filter(event=event, jenis_kelamin='putra', jenis_event='internal')
            atlet_putri_internal = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
            atlet_putra_external = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
            atlet_putri_external = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')

            # Get the URL for putra internal
            putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
            putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
            putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
            putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
            url_parts = request.path.split('/')
            internal = 'internal' in url_parts
            external = 'external' in url_parts

            context = {
                'event': event,
                'bagan_kategori': bagan_kategori,
                'kategori': kategori, 
                'atlet_putra_internal': atlet_putra_internal,
                'atlet_putri_internal': atlet_putri_internal,
                'atlet_putra_external': atlet_putra_external,
                'atlet_putri_external': atlet_putri_external,
                'putrainternal_url': putrainternal_url,
                'putriinternal_url': putriinternal_url,
                'putraexternal_url': putraexternal_url,
                'putriexternal_url': putriexternal_url,
                'internal': internal,
                'external': external,
                'num_loops1': num_loops1,
                'num_loops2': num_loops2,
                'num_loops3': num_loops3,
                'banyaknya_juri': banyaknya_juri,
            }
            return render(request, 'event/tambahbagan1.html', context)

        else:
            banyaknya_juri = request.POST.get('banyaknya_juri')

            team1_value = request.POST.getlist('team1')
            team2_value = request.POST.getlist('team2')

            event = get_object_or_404(Event, slug=event_slug)
            bgn_kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
            jenis_kelamin_display = dict(Atlet.JENIS_KELAMIN).get(jenis_kelamin)
            
            is_external = 'external' in request.path  
            
            counter = 0
            group = chr(ord('A') + counter)

            url_condition = 'External' if is_external else 'Internal'
            
            while Bagan.objects.filter(judul_bagan__icontains=f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Medali {group} - {url_condition}').exists():
                counter += 1
                group = chr(ord('A') + counter)

            judul_bagan = f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Medali {group} - {url_condition}'
            if url_condition == 'External':
                bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='external')
            else:
                bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='internal')
                
            event.id_bagan.add(bagan)
            bagan.kategori_kata.set([bgn_kategori])
            bagan.banyaknya_juri = banyaknya_juri
            bagan.save()

            for i in range(len(team1_value)):
                if team1_value[i] or team2_value[i]:
                    detail_bagan = DetailBagann.objects.create(round=1)
                    bagan.id_detailbagan.add(detail_bagan)
                    
                    for j, atlet_nama in enumerate([team1_value[i], team2_value[i]]):
                        if atlet_nama:
                            try:
                                atlet = Atlet.objects.get(id_atlet=atlet_nama)
                                detail_bagan.id_atlet.add(atlet)
                                detail_medali = DetailMedali.objects.create(number=j+1)
                                detail_bagan.perebutanjuara = f'{i+1}'
                                detail_medali.id_detailbagan = detail_bagan
                                detail_medali.id_atlet = atlet
                                detail_medali.nama = f'{atlet.nama_atlet}'
                                detail_medali.save()
                                detail_bagan.save()
                                
                            except Atlet.DoesNotExist:
                                print(f"Atlet with nama_atlet='{atlet_nama}' does not exist.")
                        else:
                            print("Empty atlet_nama encountered. Skipping...")  
            
            return redirect('keldetailkategori', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin)

class TambahBaganBendera(View):
    def post(self, request, event_slug, kategori_slug, jenis_kelamin):
        tipe = request.POST.get('tipe')
        if tipe == 'bendera':
            banyaknya_matchup = request.POST.get('value')
            banyaknya_juri = request.POST.get('juri')
            banyaknya_matchup = int(banyaknya_matchup)
            banyaknya_matchup = range(1, banyaknya_matchup + 1)
            event = get_object_or_404(Event, slug=event_slug)
            bagan = event.id_bagan.all()
            user = request.user.pk
            admin_tatami = AdminTatami.objects.filter(id_user=user).first()
            
            if admin_tatami:
                tatami = Tatami.objects.get(admin=admin_tatami)
                bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
            else:
                bagan_kategori = event.bagan_kategori.all()
            kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
            atlet_putra_internal = kategori.id_atlet.filter(event=event, jenis_kelamin='putra', jenis_event='internal')
            atlet_putri_internal = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
            atlet_putra_external = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
            atlet_putri_external = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')

            # Get the URL for putra internal
            putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
            putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
            putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
            putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
            url_parts = request.path.split('/')
            internal = 'internal' in url_parts
            external = 'external' in url_parts

            context = {
                'event': event,
                'banyaknya_matchup': banyaknya_matchup, 
                'bagan_kategori': bagan_kategori,
                'kategori': kategori, 
                'atlet_putra_internal': atlet_putra_internal,
                'atlet_putri_internal': atlet_putri_internal,
                'atlet_putra_external': atlet_putra_external,
                'atlet_putri_external': atlet_putri_external,
                'putrainternal_url': putrainternal_url,
                'putriinternal_url': putriinternal_url,
                'putraexternal_url': putraexternal_url,
                'putriexternal_url': putriexternal_url,
                'internal': internal,
                'external': external,
                'banyaknya_juri': banyaknya_juri,
            }
            return render(request, 'event/tambahbagan-bendera.html', context)

        else:
            banyaknya_juri = request.POST.get('banyaknya_juri')

            team1_value = request.POST.getlist('team1')
            team2_value = request.POST.getlist('team2')

            event = get_object_or_404(Event, slug=event_slug)
            bgn_kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
            jenis_kelamin_display = dict(Atlet.JENIS_KELAMIN).get(jenis_kelamin)
            
            is_external = 'external' in request.path  
            
            counter = 0
            group = chr(ord('A') + counter)

            url_condition = 'External' if is_external else 'Internal'
            
            while Bagan.objects.filter(judul_bagan__icontains=f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Bendera {group} - {url_condition}').exists():
                counter += 1
                group = chr(ord('A') + counter)

            judul_bagan = f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Bendera {group} - {url_condition}'
            if url_condition == 'External':
                bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='external')
            else:
                bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='internal')
                
            event.id_bagan.add(bagan)
            bagan.kategori_kata.set([bgn_kategori])
            bagan.banyaknya_juri = banyaknya_juri
            bagan.bendera = True
            bagan.save()

            for i in range(len(team1_value)):
                if team1_value[i] or team2_value[i]:
                    detail_bagan = DetailBagann.objects.create(round=1)
                    bagan.id_detailbagan.add(detail_bagan)
                    
                    for j, atlet_nama in enumerate([team1_value[i], team2_value[i]]):
                        if atlet_nama:
                            try:
                                atlet = Atlet.objects.get(id_atlet=atlet_nama)
                                detail_bagan.id_atlet.add(atlet)
                                detail_medali = DetailMedali.objects.create(number=j+1)
                                detail_bagan.perebutanjuara = f'{i+1}'
                                detail_medali.id_detailbagan = detail_bagan
                                detail_medali.id_atlet = atlet
                                detail_medali.nama = f'{atlet.nama_atlet}'
                                detail_medali.save()
                                detail_bagan.save()
                                
                            except Atlet.DoesNotExist:
                                print(f"Atlet with nama_atlet='{atlet_nama}' does not exist.")
                        else:
                            print("Empty atlet_nama encountered. Skipping...")  
            
            return redirect('keldetailkategori', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin)       

class TambahBaganNew(View):
    def post(self, request, event_slug, kategori_slug, jenis_kelamin):
        print('testestes')
        tipe = request.POST.get('tipe')
        if tipe == 'new':
            banyaknya_juri = request.POST.get('juri')

            num_loops1 = [1, 2, 3, 4]
            num_loops2 = [1, 2, 3]
            num_loops3 = [1, 2]

            round1 = [1, 2, 3, 4, 5, 6, 7, 8]
            round2 = [1, 2, 3, 4]
            round3 = [1, 2]
            round4 = [1]

            event = get_object_or_404(Event, slug=event_slug)
            bagan = event.id_bagan.all()
            user = request.user.pk
            admin_tatami = AdminTatami.objects.filter(id_user=user).first()
            
            if admin_tatami:
                tatami = Tatami.objects.get(admin=admin_tatami)
                bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
            else:
                bagan_kategori = event.bagan_kategori.all()
            kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
            atlet_putra_internal = kategori.id_atlet.filter(event=event, jenis_kelamin='putra', jenis_event='internal')
            atlet_putri_internal = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
            atlet_putra_external = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
            atlet_putri_external = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')

            # Get the URL for putra internal
            putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
            putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
            putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
            putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
            url_parts = request.path.split('/')
            internal = 'internal' in url_parts
            external = 'external' in url_parts

            print(banyaknya_juri)

            context = {
                'event': event,
                'bagan_kategori': bagan_kategori,
                'kategori': kategori, 
                'atlet_putra_internal': atlet_putra_internal,
                'atlet_putri_internal': atlet_putri_internal,
                'atlet_putra_external': atlet_putra_external,
                'atlet_putri_external': atlet_putri_external,
                'putrainternal_url': putrainternal_url,
                'putriinternal_url': putriinternal_url,
                'putraexternal_url': putraexternal_url,
                'putriexternal_url': putriexternal_url,
                'internal': internal,
                'external': external,
                'num_loops1': num_loops1,
                'num_loops2': num_loops2,
                'num_loops3': num_loops3,
                'banyaknya_juri': banyaknya_juri,
                'round1': round1,
                'round2': round2,
                'round3': round3,
                'round4': round4,
            }
            return render(request, 'event/tambahbagan2.html', context)

        else:
            banyaknya_juri = request.POST.get('banyaknya_juri')
            atletround1a = request.POST.getlist('round1a')
            atletround1b = request.POST.getlist('round1b')
            atletround2a = request.POST.getlist('round2a')
            atletround2b = request.POST.getlist('round2b')
            atletround3 = [1, 2]
            atletround4 = [1]
            atletround5 = [1]
            
            print(atletround1a)
            print(atletround1b)
            print(atletround2a)
            print(atletround2b)

            event = get_object_or_404(Event, slug=event_slug)
            bgn_kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
            jenis_kelamin_display = dict(Atlet.JENIS_KELAMIN).get(jenis_kelamin)
            
            counter = 0
            group = chr(ord('A') + counter)
            
            while Bagan.objects.filter(judul_bagan__icontains=f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Tanding {group}').exists():
                counter += 1
                group = chr(ord('A') + counter)

            judul_bagan = f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Tanding {group}'
            bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='internal')
            bagan.banyaknya_juri = banyaknya_juri
            bagan.save()

            for i in atletround3:
                db = DetailBagann.objects.create(group_tanding=i, perebutanjuara=3)
                bagan.id_detailbagan.add(db)
                bagan.save()
                
            for i in atletround4:
                db = DetailBagann.objects.create(group_tanding=i, perebutanjuara=2)
                bagan.id_detailbagan.add(db)
                bagan.save()

            for i in atletround5:
                db = DetailBagann.objects.create(group_tanding=i, perebutanjuara=1)
                bagan.id_detailbagan.add(db)
                bagan.save()

            moved = []

            group_count1 = 0
            group_count2 = 0

            for i in atletround1a:
                if i != '-':
                    atlet1 = Atlet.objects.get(pk=i)
                    detailbagan = DetailBagann.objects.create(atlet1=atlet1)
                    detailbagan.id_atlet.add(atlet1)
                    detailbagan.save()
                    detailmedali = DetailMedali.objects.create(nama=f'{atlet1}', id_detailbagan=detailbagan, id_atlet=atlet1, number=1)
                    detailmedali.save()
                else:
                    detailbagan = DetailBagann.objects.create()
                
                bagan.id_detailbagan.add(detailbagan) 
                group_count1 = group_count1 + 1
                detailbagan.group_tanding = group_count1
                detailbagan.perebutanjuara = 5
                detailbagan.save() 

                for j in atletround1b:
                    if j != '-':
                        detailbagan.atlet2 = Atlet.objects.get(pk=j)
                        atletround1b.remove(j)
                        atlet2 = Atlet.objects.get(pk=j)
                        detailbagan.id_atlet.add(atlet2)
                        detailbagan.save()
                        detailmedali = DetailMedali.objects.create(nama=f'{atlet2}', id_detailbagan=detailbagan, id_atlet=atlet2, number=2)
                        detailmedali.save()
                        break
                    else:
                        moved.append(j)
                        atletround1b.remove(j)
                        break
                
            for i in atletround2a:
                if i != '-':
                    atlet1 = Atlet.objects.get(pk=i)
                    detailbagan = DetailBagann.objects.create(atlet1=atlet1)
                    detailbagan.id_atlet.add(atlet1)
                    detailbagan.save()
                    detailmedali = DetailMedali.objects.create(nama=f'{atlet1}', id_detailbagan=detailbagan, id_atlet=atlet1, number=1)
                    detailmedali.save()
                else:
                    detailbagan = DetailBagann.objects.create()
                
                bagan.id_detailbagan.add(detailbagan) 
                group_count2 = group_count2 + 1
                detailbagan.group_tanding = group_count2
                detailbagan.perebutanjuara = 4
                detailbagan.save() 

                for j in atletround2b:
                    if j != '-':
                        detailbagan.atlet2 = Atlet.objects.get(pk=j)
                        atletround2b.remove(j)
                        atlet2 = Atlet.objects.get(pk=j)
                        detailbagan.id_atlet.add(atlet2)
                        detailbagan.save()
                        detailmedali = DetailMedali.objects.create(nama=f'{atlet2}', id_detailbagan=detailbagan, id_atlet=atlet2, number=2)
                        detailmedali.save()
                        break
                    else:
                        moved.append(j)
                        atletround2b.remove(j)
                        break

            bagan.kategori_kata.set([bgn_kategori])
            bagan.banyaknya_juri = banyaknya_juri
            bagan.new = True
            bagan.save()

            event.id_bagan.add(bagan)
            event.save()

            print('AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH')

            return redirect('keldetailkategori', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin)

class keltambahBaganTest(View):
    def post(self, request, event_slug, kategori_slug, jenis_kelamin):
        team1_value = request.POST.getlist('team1')
        team2_value = request.POST.getlist('team2')
        team3_value = request.POST.getlist('team3')
        team4_value = request.POST.getlist('team4')
        team5_value = request.POST.getlist('team5')
        team6_value = request.POST.getlist('team6')
        team7_value = request.POST.getlist('team7')
        team8_value = request.POST.getlist('team8')

        team1_kata = request.POST.getlist('team1kata')
        team2_kata = request.POST.getlist('team2kata')

        ranking = request.POST.get('ranking')

        event = get_object_or_404(Event, slug=event_slug)
        bgn_kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        jenis_kelamin_display = dict(Atlet.JENIS_KELAMIN).get(jenis_kelamin)
        
        is_external = 'external' in request.path  
          
        counter = 0
        group = chr(ord('A') + counter)

        url_condition = 'External' if is_external else 'Internal'
        
        while Bagan.objects.filter(judul_bagan__icontains=f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Medali {group} - {url_condition}').exists():
            counter += 1
            group = chr(ord('A') + counter)

        judul_bagan = f'{event} - Kata Perorangan {jenis_kelamin_display} - {bgn_kategori} - Group Medali {group} - {url_condition}'
        if url_condition == 'External':
            bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='external')
        else:
            bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kata', jenis_kelamin=jenis_kelamin, jenis_event='internal')
            
        event.id_bagan.add(bagan)
        bagan.kategori_kata.set([bgn_kategori])

        if 'group1_submit' in request.POST:
            for i in range(len(team1_value)):
                if team1_value:
                    detail_bagan = DetailBagann.objects.create(round=1)
                    bagan.id_detailbagan.add(detail_bagan)
                    print(i)
                    for atlet_id in [team1_value[i]]:
                        if atlet_id:
                            print(atlet_id)
                            try:
                                atlet = Atlet.objects.get(id_atlet=atlet_id)
                                detail_bagan.id_atlet.add(atlet)
                                detail_bagan.save()
                            except Atlet.DoesNotExist:
                                pass
                        else:
                            print('Nama atlet tidak ada...')
            bagan.tipe = "Ranking"
            bagan.save()
            return redirect('keldetailkategori', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin)
        
        else:
            # Round 1
            for i in range(len(team1_value)):
                if team1_value[i] or team2_value[i]:
                    detail_bagan = DetailBagann.objects.create(round=1)
                    bagan.id_detailbagan.add(detail_bagan)
                    
                    for j, atlet_nama in enumerate([team1_value[i], team2_value[i]]):
                        if atlet_nama:
                            try:
                                atlet = Atlet.objects.get(id_atlet=atlet_nama)
                                kata1 = team1_kata[i]
                                detail_bagan.kata1 = kata1
                                kata2 = team2_kata[i]
                                detail_bagan.kata2 = kata2
                                detail_bagan.id_atlet.add(atlet)
                                detail_medali = DetailMedali.objects.create(number=j+1)
                                detail_medali.id_detailbagan = detail_bagan
                                detail_medali.id_atlet = atlet
                                detail_medali.nama = f'{atlet.nama_atlet}'
                                detail_medali.save()
                                
                            except Atlet.DoesNotExist:
                                print(f"Atlet with nama_atlet='{atlet_nama}' does not exist.")
                        else:
                            print("Empty atlet_nama encountered. Skipping...")  
        
        return redirect('keldetailkategori', event_slug=event_slug, kategori_slug=kategori_slug, jenis_kelamin=jenis_kelamin)
    
    def get(self, request, event_slug, kategori_slug, jenis_kelamin):
        num_loops1 = [1, 2, 3, 4, 5, 6]
        num_loops2 = [1, 2, 3]
        num_loops3 = [1, 2]
        event = get_object_or_404(Event, slug=event_slug)
        bagan = event.id_bagan.all()
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()
        
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
        kategori = get_object_or_404(BaganKategori, slug=kategori_slug)
        atlet_putra_internal = kategori.id_atlet.filter(event=event, jenis_kelamin='putra', jenis_event='internal')
        atlet_putri_internal = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='internal')
        atlet_putra_external = kategori.id_atlet.filter(jenis_kelamin='putra', jenis_event='external')
        atlet_putri_external = kategori.id_atlet.filter(jenis_kelamin='putri', jenis_event='external')

        # Get the URL for putra internal
        putrainternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriinternal_url = reverse('keldetailkategoriinternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
        putraexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putra'})
        putriexternal_url = reverse('keldetailkategoriexternal', kwargs={'event_slug': event.slug, 'kategori_slug': kategori.slug, 'jenis_kelamin': 'putri'})
        url_parts = request.path.split('/')
        internal = 'internal' in url_parts
        external = 'external' in url_parts

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'kategori': kategori, 
            'atlet_putra_internal': atlet_putra_internal,
            'atlet_putri_internal': atlet_putri_internal,
            'atlet_putra_external': atlet_putra_external,
            'atlet_putri_external': atlet_putri_external,
            'putrainternal_url': putrainternal_url,
            'putriinternal_url': putriinternal_url,
            'putraexternal_url': putraexternal_url,
            'putriexternal_url': putriexternal_url,
            'internal': internal,
            'external': external,
            'num_loops1': num_loops1,
            'num_loops2': num_loops2,
            'num_loops3': num_loops3,
        }
        return render(request, 'event/tambahbagan.html', context)

# Import athletes class
class importAtlet(View):
    def post(self, request, slug):
        dataset = Dataset()
        new_data = request.FILES['file']  # Assuming the file input name is 'file'
        if not new_data.name.endswith('.xlsx'):
            messages.error(request, 'Invalid file format. Please upload an Excel file.')
            return redirect('keldetailatlet', slug=slug)

        imported_data = dataset.load(new_data.read(), format='xlsx')
        
        event = Event.objects.get(slug=slug)
        bagan = Bagan.objects.filter(event=event)
        
        for data in imported_data:
            if len(data) >= 1:  # Check if nama_atlet value exists in data
                nama_atlet = data[0]
                jenis_event = data[1]
                jenis_kelamin = data[2]
                perguruan = data[3]
                perwakilan = data[4]
                tempat_lahir = data[5]
                tanggal_lahir = data[6]
                usia_atlet = data[7]
                berat_badan = data[8]
                atlet = Atlet(
                    nama_atlet=nama_atlet,
                    jenis_event=jenis_event,
                    jenis_kelamin=jenis_kelamin,
                    perguruan=perguruan,
                    perwakilan=perwakilan,
                    tempat_lahir=tempat_lahir,
                    tanggal_lahir=tanggal_lahir,
                    usia_atlet=usia_atlet,
                    berat_badan=berat_badan,
                )
                atlet.save()
                event.id_atlet.add(atlet)
                event.save()
            
            # Validasi Usia
            if usia_atlet is not None:
                if atlet.usia_atlet <= 7.9:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Pra Usia Dini')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                if atlet.usia_atlet >= 8 and atlet.usia_atlet <= 9.9:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Usia Dini')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                if atlet.usia_atlet >= 10 and atlet.usia_atlet <= 11.9:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Pra Pemula')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                if atlet.usia_atlet >= 12 and atlet.usia_atlet <= 13.9:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Pemula')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                if atlet.usia_atlet >= 14:
                    bagan_kategori, created = BaganKategori.objects.get_or_create(event=event, judul_kategori='Kadet')
                    event.bagan_kategori.add(bagan_kategori)
                    bagan_kategori.id_atlet.add(atlet)
                    event.save()
                
        messages.success(request, 'Data imported successfully.')
        return redirect('keldetailatlet', slug=slug)
    
# Dummy
class dummy(View):
    def get(self, request):
        return render(request, 'event/scoringboardtest.html')

    def post(self, request):
        team1_kata = request.POST.get('team1kata')
        print(team1_kata)

        return redirect('dummy')

class CreateBaganKumite(View):
    def get(self, request, event_slug):
        event = get_object_or_404(Event, slug=event_slug)
        bagan = event.id_bagan.all()
        user = request.user.pk
        admin_tatami = AdminTatami.objects.filter(id_user=user).first()

        round1 = [1, 2, 3, 4, 5, 6, 7, 8]
        round2 = [1, 2, 3, 4]
        round3 = [1, 2]
        round4 = [1]
    
        if admin_tatami:
            tatami = Tatami.objects.get(admin=admin_tatami)
            bagan_kategori = BaganKategori.objects.filter(tatami_nomor_tanding=tatami)
        else:
            bagan_kategori = event.bagan_kategori.all()
            tatami = 'Tatami'

        context = {
            'event': event,
            'bagan_kategori': bagan_kategori,
            'tatami': tatami,
            'round1': round1,
            'round2': round2,
            'round3': round3,
            'round4': round4,
        }

        return render(request, 'event/bagankumite.html', context)

    def post(self, request, event_slug):
        form_type = request.POST.get('form_type')
        event = Event.objects.get(slug=event_slug)
        
        if form_type == 'tambahbaganform':
            nomor_tanding = request.POST.get('nomor_tanding')
            if nomor_tanding != '-':
                nomor_tanding = BaganKategori.objects.get(pk=nomor_tanding)
                user = request.user.pk
                admin_tatami = AdminTatami.objects.filter(id_user=user).first()
                atlets = nomor_tanding.id_atlet.all()

                round1 = [1, 2, 3, 4, 5, 6, 7, 8]
                round2 = [1, 2, 3, 4]
                round3 = [1, 2]
                round4 = [1]

                context = {
                    'event': event,
                    'nomor_tanding': nomor_tanding,
                    'round1': round1,
                    'round2': round2,
                    'round3': round3,
                    'round4': round4,
                    'atlets': atlets,
                }
                return render(request, 'event/bagankumite.html', context)
            else:
                return redirect('kumite-home', slug=event_slug)
        elif form_type == 'submit_bagan':
            atletround1a = request.POST.getlist('round1a')
            atletround1b = request.POST.getlist('round1b')
            atletround2a = request.POST.getlist('round2a')
            atletround2b = request.POST.getlist('round2b')
            nomor_tanding = request.POST.get('nomor_tanding')
            nomor_tanding = BaganKategori.objects.get(pk=nomor_tanding)

            print(atletround1a)
            print(atletround1b)
            print(atletround2a)
            print(atletround2b)
            print(nomor_tanding)

            counter = 0
            group = chr(ord('A') + counter)
            
            while Bagan.objects.filter(judul_bagan__icontains=f'{event} - Kumite {nomor_tanding} - Group Tanding {group}').exists():
                counter += 1
                group = chr(ord('A') + counter)

            judul_bagan = f'{event} - Kumite {nomor_tanding} - Group Tanding {group}'
            bagan = Bagan.objects.create(judul_bagan=judul_bagan, kategori='kumite', jenis_event='internal')
            bagan.save()

            moved = []

            group_count1 = 0
            group_count2 = 0

            for i in atletround1a:
                if i != '-':
                    atlet1 = Atlet.objects.get(pk=i)
                    detailbagan = DetailBagann.objects.create(atlet1=atlet1)
                    detailbagan.id_atlet.add(atlet1)
                    detailbagan.save()
                    detailmedali = DetailMedali.objects.create(nama=f'{atlet1}', id_detailbagan=detailbagan, id_atlet=atlet1, number=1)
                    detailmedali.save()
                else:
                    detailbagan = DetailBagann.objects.create()
                
                bagan.id_detailbagan.add(detailbagan) 
                group_count1 = group_count1 + 1
                detailbagan.group_tanding = group_count1
                detailbagan.perebutanjuara = 5
                detailbagan.save() 

                for j in atletround1b:
                    if j != '-':
                        detailbagan.atlet2 = Atlet.objects.get(pk=j)
                        atletround1b.remove(j)
                        atlet2 = Atlet.objects.get(pk=j)
                        detailbagan.id_atlet.add(atlet2)
                        detailbagan.save()
                        detailmedali = DetailMedali.objects.create(nama=f'{atlet2}', id_detailbagan=detailbagan, id_atlet=atlet2, number=2)
                        detailmedali.save()
                        break
                    else:
                        moved.append(j)
                        atletround1b.remove(j)
                        break
                
            for i in atletround2a:
                if i != '-':
                    atlet1 = Atlet.objects.get(pk=i)
                    detailbagan = DetailBagann.objects.create(atlet1=atlet1)
                    detailbagan.id_atlet.add(atlet1)
                    detailbagan.save()
                    detailmedali = DetailMedali.objects.create(nama=f'{atlet1}', id_detailbagan=detailbagan, id_atlet=atlet1, number=1)
                    detailmedali.save()
                else:
                    detailbagan = DetailBagann.objects.create()
                
                bagan.id_detailbagan.add(detailbagan) 
                group_count2 = group_count2 + 1
                detailbagan.group_tanding = group_count2
                detailbagan.perebutanjuara = 4
                detailbagan.save() 

                for j in atletround2b:
                    if j != '-':
                        detailbagan.atlet2 = Atlet.objects.get(pk=j)
                        atletround2b.remove(j)
                        atlet2 = Atlet.objects.get(pk=j)
                        detailbagan.id_atlet.add(atlet2)
                        detailbagan.save()
                        detailmedali = DetailMedali.objects.create(nama=f'{atlet2}', id_detailbagan=detailbagan, id_atlet=atlet2, number=2)
                        detailmedali.save()
                        break
                    else:
                        moved.append(j)
                        atletround2b.remove(j)
                        break

            bagan.kategori_kata.set([nomor_tanding])
            bagan.new = True
            bagan.save()

            event.id_bagan.add(bagan)
            event.save()

            atletround3 = [1, 2]
            atletround4 = [1]
            atletround5 = [1]

            for i in atletround3:
                db = DetailBagann.objects.create(group_tanding=i, perebutanjuara=3)
                bagan.id_detailbagan.add(db)
                bagan.save()
                
            for i in atletround4:
                db = DetailBagann.objects.create(group_tanding=i, perebutanjuara=2)
                bagan.id_detailbagan.add(db)
                bagan.save()

            for i in atletround5:
                db = DetailBagann.objects.create(group_tanding=i, perebutanjuara=1)
                bagan.id_detailbagan.add(db)
                bagan.save()

            return redirect('kumite-home', slug=event_slug)
        else:
            return redirect('kumite-home', slug=event_slug)

class BaganKumiteView(View):
    def get(self, request, slug, bagan_pk):
        event = Event.objects.get(slug=slug)
        bagan = Bagan.objects.get(pk=bagan_pk)

        round_1 = bagan.id_detailbagan.filter(perebutanjuara=5).order_by('group_tanding')
        round_2 = bagan.id_detailbagan.filter(perebutanjuara=4).order_by('group_tanding')
        round_3 = bagan.id_detailbagan.filter(perebutanjuara=3).order_by('group_tanding')
        round_4 = bagan.id_detailbagan.filter(perebutanjuara=2).order_by('group_tanding')
        round_5 = bagan.id_detailbagan.filter(perebutanjuara=1).order_by('group_tanding').first()

        context = {
            'event': event,
            'round_1': round_1,
            'round_2': round_2,
            'round_3': round_3,
            'round_4': round_4,
            'round_5': round_5,
        }
        return render(request, 'event/baganview.html', context)
    
    def post(self, request, slug, bagan_pk):
        bagan = Bagan.objects.get(pk=bagan_pk)
        aka_pk = request.POST.get('aka-contestant')
        aka_score = request.POST.get('aka-score')
        ao_pk = request.POST.get('ao-contestant')
        ao_score = request.POST.get('ao-score')
        detail_bagan = request.POST.get('detail_bagan1')
        penentuan = request.POST.get('penentuan')

        print(penentuan)
        
        detailbagan = DetailBagann.objects.get(pk=detail_bagan)
        detailbagan.score1 = aka_score
        detailbagan.score2 = ao_score
        detailbagan.save()

        score1 = aka_score
        score2 = ao_score

        if detailbagan.group_tanding == 1 and detailbagan.perebutanjuara == 5:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                new_detailbagan.atlet1 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                new_detailbagan.atlet1 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        elif detailbagan.group_tanding == 2 and detailbagan.perebutanjuara == 5:
            if penentuan == '-':    
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
            
            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                new_detailbagan.atlet2 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=4)
                new_detailbagan.atlet2 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        elif detailbagan.group_tanding == 3 and detailbagan.perebutanjuara == 5:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
            
            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                new_detailbagan.atlet1 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                new_detailbagan.atlet1 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()
            
        elif detailbagan.group_tanding == 4 and detailbagan.perebutanjuara == 5:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
            
            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                new_detailbagan.atlet2 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=4)
                new_detailbagan.atlet2 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        elif detailbagan.group_tanding == 5 and detailbagan.perebutanjuara == 5:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                new_detailbagan.atlet1 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                new_detailbagan.atlet1 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        elif detailbagan.group_tanding == 6 and detailbagan.perebutanjuara == 5:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                new_detailbagan.atlet2 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=3, perebutanjuara=4)
                new_detailbagan.atlet2 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()
            
        elif detailbagan.group_tanding == 7 and detailbagan.perebutanjuara == 5:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                new_detailbagan.atlet1 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                new_detailbagan.atlet1 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        elif detailbagan.group_tanding == 8 and detailbagan.perebutanjuara == 5:
            if penentuan == '-': 
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
            
            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                new_detailbagan.atlet2 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=4, perebutanjuara=4)
                new_detailbagan.atlet2 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        if detailbagan.group_tanding == 1 and detailbagan.perebutanjuara == 4:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()
            
            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                new_detailbagan.atlet1 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                new_detailbagan.atlet1 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        elif detailbagan.group_tanding == 2 and detailbagan.perebutanjuara == 4:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                new_detailbagan.atlet2 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=3)
                new_detailbagan.atlet2 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()


        elif detailbagan.group_tanding == 3 and detailbagan.perebutanjuara == 4:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                new_detailbagan.atlet1 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                new_detailbagan.atlet1 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()
            
        elif detailbagan.group_tanding == 4 and detailbagan.perebutanjuara == 4:
            if penentuan == '-':    
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                new_detailbagan.atlet2 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=2, perebutanjuara=3)
                new_detailbagan.atlet2 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()
        
        if detailbagan.group_tanding == 1 and detailbagan.perebutanjuara == 3:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                    new_detailbagan.atlet1 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                    new_detailbagan.atlet1 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                new_detailbagan.atlet1 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()
            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                new_detailbagan.atlet1 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        elif detailbagan.group_tanding == 2 and detailbagan.perebutanjuara == 3:
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                new_detailbagan.atlet2 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=2)
                new_detailbagan.atlet2 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        if detailbagan.group_tanding == 1 and detailbagan.perebutanjuara == 2:
            print(penentuan)
            if penentuan == '-':
                if score1 > score2:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=1)
                    new_detailbagan.atlet2 = detailbagan.atlet1
                    new_detailbagan.id_atlet.add(detailbagan.atlet1)
                    new_detailbagan.save()
                    
                elif score2 > score1:
                    new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=1)
                    new_detailbagan.atlet2 = detailbagan.atlet2
                    new_detailbagan.id_atlet.add(detailbagan.atlet2)
                    new_detailbagan.save()

            elif penentuan == 'aka':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=1)
                new_detailbagan.atlet2 = detailbagan.atlet1
                new_detailbagan.id_atlet.add(detailbagan.atlet1)
                new_detailbagan.save()

            elif penentuan == 'ao':
                new_detailbagan = bagan.id_detailbagan.get(group_tanding=1, perebutanjuara=1)
                new_detailbagan.atlet2 = detailbagan.atlet2
                new_detailbagan.id_atlet.add(detailbagan.atlet2)
                new_detailbagan.save()

        return redirect('bagan-kumite-view', slug=slug, bagan_pk=bagan_pk)
    
        
    


# note:
# - membuat tampilan bagi guest untuk kumite