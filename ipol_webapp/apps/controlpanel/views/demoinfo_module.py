from crispy_forms.utils import render_crispy_form
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
from django.http import HttpResponse
from apps.controlpanel.forms import DDLform, Demoform, Authorform
from apps.controlpanel.mixings import NavbarReusableMixinMF

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView
from apps.controlpanel.tools import get_status_and_error_from_json
from apps.controlpanel.views.ipolwebservices.ipoldeserializers import DeserializeDemoinfoDemoList, \
	DeserializeDemoinfoAuthorList
from apps.controlpanel.views.ipolwebservices import ipolservices
import logging
from apps.controlpanel.views.ipolwebservices.ipolservices import is_json, demoinfo_get_states

logger = logging.getLogger(__name__)

__author__ = 'josearrecio'


PAGINATION_ITEMS_PER_PAGE_DEMO_LIST = 4
PAGINATION_ITEMS_PER_PAGE_AUTHOR_LIST = 4
PAGINATION_ITEMS_PER_PAGE_EDITOR_LIST = 4


# demos

class DemoinfoDemosView(NavbarReusableMixinMF,TemplateView):
	template_name = "demoinfo/demoinfo_demos.html"


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		# para las pestanas
		self.request.session['topmenu'] = 'topmenu-demoinfo-demos'
		return super(DemoinfoDemosView, self).dispatch(*args, **kwargs)


	def get_context_data(self, **kwargs):

		#get context
		context = super(DemoinfoDemosView, self).get_context_data(**kwargs)

		try:
			#get data from WS, paginate and filter in CP
			#dl = ipolservices.demoinfo_demo_list()
			# if dl:
			# 	result = DeserializeDemoinfoDemoList(dl)
			# else:
			# 	raise ValueError("No response from WS")
			#
			# list_demos = result.demo_list
			# status = result.status
			#
			# #filter result
			# query = self.request.GET.get('q')
			# # print "query",query
			# list_demos_filtered = list()
			# if query:
			# 	for demo in list_demos:
			# 		# print "demo: ",demo
			# 		if query in demo.title or query in demo.abstract :
			# 			print "ok"
			# 			list_demos_filtered.append(demo)
			#
			# 	list_demos = list_demos_filtered
			# context['q'] = query
			#
			# #pagination of result
			# paginator = Paginator(list_demos, PAGINATION_ITEMS_PER_PAGE_DEMO_LIST)
			# page = self.request.GET.get('page')
			# try:
			# 	list_demos = paginator.page(page)
			# except PageNotAnInteger:
			# 	# If page is not an integer, deliver first page.
			# 	list_demos = paginator.page(1)
			# except EmptyPage:
			# 	# If page is out of range (e.g. 9999), deliver last page of results.
			# 	list_demos = paginator.page(paginator.num_pages)

			#get data from WS paginated and filtered


			#filter result
			query = self.request.GET.get('q')
			context['q'] = query
			try:
				page = self.request.GET.get('page')
				page = int(page)
			except :
				# If page is not an integer, deliver first page.
				page = 1


			dl = ipolservices.demoinfo_demo_list_pagination_and_filtering(PAGINATION_ITEMS_PER_PAGE_DEMO_LIST,page,query)
			if dl:
				result = DeserializeDemoinfoDemoList(dl)
			else:
				raise ValueError("No response from WS")

			list_demos = result.demo_list

			#print "list_demos",list_demos
			status = result.status

			#pagination of result
			if hasattr(result, 'previous_page_number'):
				context['previous_page_number'] = result.previous_page_number
				context['has_previous'] = True
			else:
				context['has_previous'] = False

			if page:
				context['number'] = page

			if hasattr(result, 'number'):
				context['num_pages'] = result.number

			if hasattr(result, 'next_page_number'):
				context['next_page_number'] = result.next_page_number
				context['has_next'] = True
			else:
				context['has_next'] = False


			#send context vars for template
			context['status'] = status
			context['list_demos'] = list_demos
			context['ddlform'] = DDLform
			context['demoform'] = Demoform
			#context['demoform'] = Demoform(initial={'active': True})

		except Exception as e:

			msg=" DemoinfoDemosView Error %s "%e
			logger.error(msg)
			context['status'] = 'KO'
			context['list_demos'] = []
			context['ddlform'] = None
			context['demoform'] = None
			logger.error(msg)
			print(msg)


		return context


class DemoinfoDeleteDemoView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DemoinfoDeleteDemoView, self).dispatch(*args, **kwargs)

	def post(self, request, *args, **kwargs):

			#todo could validate a form to get hard_delete checkbox from user
			try:
				demo_id = int(self.kwargs['demo_id'])
			except ValueError:
				msg= "Id is not an integer"
				logger.error(msg)
				raise ValueError(msg)

			result= ipolservices.demoinfo_delete_demo(demo_id,hard_delete = False)
			if result == None:
				msg="DemoinfoDeleteDemoView: Something went wrong using demoinfo WS"
				logger.error(msg)
				raise ValueError(msg)

			print result

			return HttpResponse(result, content_type='application/json')


class DemoinfoGetDDLView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DemoinfoGetDDLView, self).dispatch(*args, **kwargs)

	def post(self, *args, **kwargs):


			try:
				demo_id = int(self.kwargs['demo_id'])
			except ValueError:
				msg= "Id is not an integer"
				logger.error(msg)
				raise ValueError(msg)


			result= ipolservices.demoinfo_read_last_demodescription_from_demo(demo_id,returnjsons=True)
			if result == None:
				msg="DemoinfoGetDDLView: Something went wrong using demoinfo WS"
				print msg
				logger.error(msg)
				#raise ValueError(msg)
				data=dict()
				data["status"] = "KO"
				data["error"] = "msg"


			import json
			#your_json = '["foo", {"bar":["baz", null, 1.0, 2]}]'
			# parsed = json.loads(result)
			# result = json.dumps(parsed, indent=4, sort_keys=True)

			# print "result: ",result
			# print "result type: ",type(result)

			return HttpResponse(result,content_type='application/json')


class DemoinfoSaveDDLView(NavbarReusableMixinMF,FormView):

	template_name = ''
	form_class = DDLform

	def form_valid(self, form):
		"""
		If the request is ajax, save the form and return a json response.
		Otherwise return super as expected.
		"""
		jres=dict()
		jres['status'] = 'KO'

		if self.request.is_ajax():

			print "valid ajax form"

			# get form fields and send info to be saved in demoinfo
			demoid = None
			ddlid = None
			ddlJSON = None
			try:
				ddlid = form.cleaned_data['ddlid']
				ddlid = int(ddlid)
				# print " ddlid ",ddlid
				#print " json.dumps(ddlJSON) ",json.dumps(ddlJSON, indent=4)
			except Exception:
				ddlid = None
			try:
				demoid = form.cleaned_data['demoid']
				demoid = int(demoid)
				ddlJSON = form.cleaned_data['ddlJSON']
				# print " demoid ",demoid
				# print " ddlJSON ",ddlJSON[-50:]
				#print " json.dumps(ddlJSON) ",json.dumps(ddlJSON, indent=4)
			except Exception as e:
				msg = "DemoinfoSaveDDLView form: %s" % e
				print msg
				logger.error(msg)

			# save
			if ddlJSON is not None:

				print "is_json(ddlJSON)",is_json(ddlJSON)
				if is_json(ddlJSON):

					if ddlid is None :
						try:
							# print (" create ddl")
							jsonresult = ipolservices.demoinfo_add_demo_description(pjson=ddlJSON,demoid=demoid)
							status,error = get_status_and_error_from_json(jsonresult)
							jres['status'] = status
							if error is not None:
									jres['error'] = error

						except Exception as e:
							msg = "update ddl error: %s" % e
							logger.error(msg)
							print msg
					else:
						try:
							# print (" update ddl ")
							jsonresult= ipolservices.demoinfo_update_demo_description(ddlid,pjson=ddlJSON)
							status,error = get_status_and_error_from_json(jsonresult)
							jres['status'] = status
							if error is not None:
									jres['error'] = error
						except Exception as e:
							msg = "update ddl error: %s" % e
							logger.error(msg)
							print msg
				else:
					msg='DemoinfoSaveDDLView invalid json'
					logger.warning(msg)
					jres['error'] = msg
			else:
				msg='DemoinfoSaveDDLView no json found'
				logger.warning(msg)
				jres['error'] = msg
		else:
			jres['error'] = 'form_valid no ajax'
			#print "check Jquery form submit, something is wrong with ajax call"
			logger.warning('DemoinfoSaveDDLView form_valid ,but no ajax')

		return HttpResponse(json.dumps(jres),content_type='application/json')
		#
		# print "not valid ajax form"
		# return super(DemoinfoSaveDDLView, self).form_valid(form)

	def form_invalid(self, form):
		"""
		We haz errors in the form. If ajax, return them as json.
		Otherwise, proceed as normal.
		"""
		jres = dict()
		if self.request.is_ajax():

			print "invalid ajax form"
			print form.errors
			print form

			#form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
			# form_html = render_crispy_form(form)
			# logger.warning(form_html)

			jres['form_html'] = str(form.errors)
			jres['status'] = 'KO'
		else:
			jres['status'] = 'form_invalid no ajax'
			logger.warning('form_invalid no ajax')

		#return HttpResponseBadRequest(json.dumps(form.errors),mimetype="application/json")
		return HttpResponse(json.dumps(jres),content_type='application/json')
		# return super(DemoinfoSaveDDLView, self).form_invalid(form)


class DemoinfoGetDemoView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DemoinfoGetDemoView, self).dispatch(*args, **kwargs)

	def post(self, *args, **kwargs):

			# print "DemoinfoGetDemoView"
			try:
				demo_id = int(self.kwargs['demo_id'])
			except ValueError:
				msg= "Id is not an integer"
				logger.error(msg)
				raise ValueError(msg)

			result= ipolservices.demoinfo_read_demo(demo_id)
			if result == None:
				msg="DemoinfoGetDemoView: Something went wrong using demoinfo WS"
				logger.error(msg)
				raise ValueError(msg)


			# print "Demoinfo  DemoinfoGetDemoView result: ",result
			# print "result type: ",type(result)

			return HttpResponse(result,content_type='application/json')


class DemoinfoSaveDemoView(NavbarReusableMixinMF,FormView):

	template_name = ''
	form_class = Demoform


	def form_valid(self, form):

		jres = dict()
		jres['status'] = 'KO'

		"""
		If the request is ajax, save the form and return a json response.
		Otherwise return super as expected.
		"""
		if self.request.is_ajax():

			# print "valid ajax form"
			# print form
			# print

			# get form fields
			id = None
			title = None
			abstract = None
			stateID = None
			editorsdemoid = None
			active = None
			zipURL = None
			# creation = None
			# modification = None
			# if form has id field set, I must update, if not, create a new demo
			try:
				id = form.cleaned_data['id']
				id = int(id)
				print " id ",id
			except Exception :
				print "AKI"
				id = None

			try:
				title = form.cleaned_data['title']
				abstract = form.cleaned_data['abstract']
				stateID = form.cleaned_data['state']
				stateID = int(stateID)
				editorsdemoid = form.cleaned_data['editorsdemoid']
				editorsdemoid = int(editorsdemoid)
				#active = form.cleaned_data['active']
				zipURL = form.cleaned_data['zipURL']
				# creation = form.cleaned_data['creation']
				# modification = form.cleaned_data['modification']
				print " title ",title
				print " active ",active, type(active)
				print
				#print " json.dumps(ddlJSON) ",json.dumps(ddlJSON, indent=4)
			except Exception as e:
				msg = "DemoinfoSaveDemoView form data error: %s" % e
				print msg
				logger.error(msg)

			#  send info to be saved in demoinfo module
			# save
			if id is None :

				try:
					# print (" create demo")
					# print

					jsonresult= ipolservices.demoinfo_add_demo(editorsdemoid ,title ,abstract,zipURL ,True ,stateID)
					print "jsonresult", jsonresult
					status,error = get_status_and_error_from_json(jsonresult)
					jres['status'] = status
					if error is not None:
							jres['error'] = error

				except Exception as e:
					msg = "create demo error: %s" % e
					jres['error'] = msg
					logger.error(msg)
					print msg
			else:
				try:
					# print (" update demo ")
					# print
					demojson = {
								"title": title,
								"abstract": abstract,
								"editorsdemoid": editorsdemoid,
								"active": True,
								"stateID": stateID,
								"id": id,
								"zipURL": zipURL,
								# "creation": creation,
								# "modification": modification
					}
					jsonresult = ipolservices.demoinfo_update_demo(demojson)
					status,error = get_status_and_error_from_json(jsonresult)
					jres['status'] = status
					if error is not None:
							jres['error'] = error

					#TODO todos los WS deben devolver status y errors, asi se lo paso directamente al html
				except Exception as e:
					msg = "update demo error: %s" % e
					jres['error'] = msg
					logger.error(msg)
					print msg

		else:
			jres['error'] = 'form_valid no ajax'
			logger.warning('DemoinfoSaveDemoView form_valid no ajax')


		return HttpResponse(json.dumps(jres),content_type='application/json')
		#
		# print "not valid ajax form"
		# return super(DemoinfoSaveDDLView, self).form_valid(form)

	def form_invalid(self, form):
		"""
		We haz errors in the form. If ajax, return them as json.
		Otherwise, proceed as normal.
		"""
		jres = dict()
		if self.request.is_ajax():

			# print " ---invalid ajax form"
			# print form.errors
			# print form

			#form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
			# form_html = render_crispy_form(form)
			# logger.warning(form_html)

			jres['form_html'] = str(form.errors)
			jres['status'] = 'KO'

		else:
			jres['status'] = 'form_invalid no ajax'
			logger.warning('form_invalid no ajax')

		#return HttpResponseBadRequest(json.dumps(form.errors),mimetype="application/json")
		return HttpResponse(json.dumps(jres),content_type='application/json')
		# return super(DemoinfoSaveDDLView, self).form_invalid(form)

#authors

class DemoinfoAuthorsView(NavbarReusableMixinMF,TemplateView):
	template_name = "demoinfo/demoinfo_authors.html"


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		# para las pestanas
		self.request.session['topmenu'] = 'topmenu-demoinfo-authors'
		return super(DemoinfoAuthorsView, self).dispatch(*args, **kwargs)

	def get_context_data(self, **kwargs):

		#get context
		context = super(DemoinfoAuthorsView, self).get_context_data(**kwargs)

		try:

			#filter result
			query = self.request.GET.get('q')
			context['q'] = query
			try:
				page = self.request.GET.get('page')
				page = int(page)
			except :
				# If page is not an integer, deliver first page.
				page = 1

			al = ipolservices.demoinfo_author_list_pagination_and_filtering(PAGINATION_ITEMS_PER_PAGE_AUTHOR_LIST,page,query)
			if al:
				result = DeserializeDemoinfoAuthorList(al)
			else:
				raise ValueError("No response from WS")

			list_authors = result.author_list

			print "list_authors",list_authors
			status = result.status

			#pagination of result
			if hasattr(result, 'previous_page_number'):
				context['previous_page_number'] = result.previous_page_number
				context['has_previous'] = True
			else:
				context['has_previous'] = False

			if page:
				context['number'] = page

			if hasattr(result, 'number'):
				context['num_pages'] = result.number

			if hasattr(result, 'next_page_number'):
				context['next_page_number'] = result.next_page_number
				context['has_next'] = True
			else:
				context['has_next'] = False


			#send context vars for template
			context['status'] = status
			context['list_authors'] = list_authors
			context['authorform'] = Authorform
			#context['demoform'] = Demoform(initial={'active': True})

		except Exception as e:

			msg=" DemoinfoAuthorformView Error %s "%e
			logger.error(msg)
			context['status'] = 'KO'
			context['list_authors'] = []
			context['authorform'] = None
			logger.error(msg)
			print(msg)


		return context


class DemoinfoDeleteAuthorView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DemoinfoDeleteAuthorView, self).dispatch(*args, **kwargs)

	def post(self, request, *args, **kwargs):

			#todo could validate a form to get hard_delete checkbox from user
			try:
				author_id = int(self.kwargs['author_id'])
			except ValueError:
				msg= "Id is not an integer"
				logger.error(msg)
				raise ValueError(msg)

			result= ipolservices.demoinfo_delete_author(author_id)
			if result == None:
				msg="DemoinfoDeleteAuthorView: Something went wrong using demoinfo WS"
				logger.error(msg)
				raise ValueError(msg)

			print result

			return HttpResponse(result, content_type='application/json')


class DemoinfoGetAuthorView(NavbarReusableMixinMF,TemplateView):

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DemoinfoGetAuthorView, self).dispatch(*args, **kwargs)

	def post(self, *args, **kwargs):
			# print "DemoinfoGetAuthorView"
			try:
				author_id = int(self.kwargs['author_id'])
			except ValueError:
				msg= "Id is not an integer"
				logger.error(msg)
				raise ValueError(msg)

			result= ipolservices.demoinfo_read_author(author_id)
			if result == None:
				msg="DemoinfoGetAuthorView: Something went wrong using demoinfo WS"
				logger.error(msg)
				raise ValueError(msg)


			# print "Demoinfo  DemoinfoGetAuthorView result: ",result
			# print "result type: ",type(result)

			return HttpResponse(result,content_type='application/json')

# mucho ojo con el FormView!! como uses templatevie por error, la llamada ajax falla de forma raras :)
class DemoinfoSaveAuthorView(NavbarReusableMixinMF,FormView):

	template_name = ''
	form_class = Authorform


	def form_valid(self, form):

		jres = dict()
		jres['status'] = 'KO'

		# print "valid form"


		if self.request.is_ajax():

			# print "valid ajax form"
			# print form
			# print

			# get form fields
			id = None
			name = None
			mail = None
			# creation = None
			# if form has id field set, I must update, if not, create a new demo
			try:
				id = form.cleaned_data['id']
				id = int(id)
				print " id ",id
			except Exception :
				id = None
			try:
				name = form.cleaned_data['name']
				mail = form.cleaned_data['mail']
				# print " name ",name
				# print
				#print " json.dumps(ddlJSON) ",json.dumps(ddlJSON, indent=4)
			except Exception as e:
				msg = "DemoinfoSaveAuthorView form data error: %s" % e
				print msg
				logger.error(msg)

			#  send info to be saved in demoinfo module
			# save
			if id is None :

				try:
					# print (" create author")
					# print

					jsonresult = ipolservices.demoinfo_add_author(name,mail)
					print "jsonresult", jsonresult
					status,error = get_status_and_error_from_json(jsonresult)
					jres['status'] = status
					if error is not None:
							jres['error'] = error

				except Exception as e:
					msg = "create author error: %s" % e
					jres['error'] = msg
					logger.error(msg)
					print msg
			else:
				try:
					print (" update author ")
					print
					demojson = {
								"id": id,
								"name": name,
								"mail": mail
								# "creation": creation
					}
					jsonresult = ipolservices.demoinfo_update_author(demojson)
					status,error = get_status_and_error_from_json(jsonresult)
					jres['status'] = status
					if error is not None:
							jres['error'] = error
							print jres['error']

					#TODO todos los WS deben devolver status y errors, asi se lo paso directamente al html
				except Exception as e:
					msg = "update author error: %s" % e
					jres['error'] = msg
					logger.error(msg)
					print msg

		else:
			jres['error'] = 'form_valid no ajax'
			logger.warning('DemoinfoSaveAuthorView form_valid no ajax')


		return HttpResponse(json.dumps(jres),content_type='application/json')


	def form_invalid(self, form):

		jres = dict()
		jres['status'] = 'KO'
		print "invalid form"

		if self.request.is_ajax():

			print " ---invalid ajax form"
			print form.errors
			print form

			#form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
			# form_html = render_crispy_form(form)
			# logger.warning(form_html)

			jres['error'] = str(form.errors)
			jres['status'] = 'KO'

		else:
			jres['error'] = 'form_invalid no ajax'
			logger.warning('form_invalid no ajax')

		return HttpResponse(json.dumps(jres),content_type='application/json')


# demo-authors
class DemoinfoDeleteAuthorFromDemoView(NavbarReusableMixinMF,TemplateView):
	pass

	# @method_decorator(login_required)
	# def dispatch(self, *args, **kwargs):
	# 	return super(DemoinfoDeleteAuthorView, self).dispatch(*args, **kwargs)
	#
	# def post(self, request, *args, **kwargs):
	#
	# 		#todo could validate a form to get hard_delete checkbox from user
	# 		try:
	# 			author_id = int(self.kwargs['author_id'])
	# 		except ValueError:
	# 			msg= "Id is not an integer"
	# 			logger.error(msg)
	# 			raise ValueError(msg)
	#
	# 		result= ipolservices.demoinfo_delete_author(author_id)
	# 		if result == None:
	# 			msg="DemoinfoDeleteAuthorView: Something went wrong using demoinfo WS"
	# 			logger.error(msg)
	# 			raise ValueError(msg)
	#
	# 		print result
	#
	# 		return HttpResponse(result, content_type='application/json')


class DemoinfoGetDemoAuthorView(NavbarReusableMixinMF,TemplateView):

	"""
	Must return:

	-List of the authos of a demo
	-Authorselection form, initialized whith the available authors, so you can select one and add it to the demo
	"""

	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(DemoinfoGetDemoAuthorView, self).dispatch(*args, **kwargs)

	def post(self, *args, **kwargs):
			# print "DemoinfoGetAuthorView"
			try:
				author_id = int(self.kwargs['author_id'])
			except ValueError:
				msg= "Id is not an integer"
				logger.error(msg)
				raise ValueError(msg)

			result= ipolservices.demoinfo_read_author(author_id)
			if result == None:
				msg="DemoinfoGetDemoAuthorView: Something went wrong using demoinfo WS"
				logger.error(msg)
				raise ValueError(msg)


			# print "Demoinfo  DemoinfoGetAuthorView result: ",result
			# print "result type: ",type(result)

			return HttpResponse(result,content_type='application/json')

class DemoinfoAddAuthorToDemoView(NavbarReusableMixinMF,FormView):
	pass
	#
	# template_name = ''
	# form_class = Authorform
	#
	#
	# def form_valid(self, form):
	#
	# 	jres = dict()
	# 	jres['status'] = 'KO'
	#
	# 	# print "valid form"
	#
	#
	# 	if self.request.is_ajax():
	#
	# 		# print "valid ajax form"
	# 		# print form
	# 		# print
	#
	# 		# get form fields
	# 		id = None
	# 		name = None
	# 		mail = None
	# 		# creation = None
	# 		# if form has id field set, I must update, if not, create a new demo
	# 		try:
	# 			id = form.cleaned_data['id']
	# 			id = int(id)
	# 			print " id ",id
	# 		except Exception :
	# 			id = None
	# 		try:
	# 			name = form.cleaned_data['name']
	# 			mail = form.cleaned_data['mail']
	# 			# print " name ",name
	# 			# print
	# 			#print " json.dumps(ddlJSON) ",json.dumps(ddlJSON, indent=4)
	# 		except Exception as e:
	# 			msg = "DemoinfoSaveAuthorView form data error: %s" % e
	# 			print msg
	# 			logger.error(msg)
	#
	# 		#  send info to be saved in demoinfo module
	# 		# save
	# 		if id is None :
	#
	# 			try:
	# 				# print (" create author")
	# 				# print
	#
	# 				jsonresult = ipolservices.demoinfo_add_author(name,mail)
	# 				print "jsonresult", jsonresult
	# 				status,error = get_status_and_error_from_json(jsonresult)
	# 				jres['status'] = status
	# 				if error is not None:
	# 						jres['error'] = error
	#
	# 			except Exception as e:
	# 				msg = "create author error: %s" % e
	# 				jres['error'] = msg
	# 				logger.error(msg)
	# 				print msg
	# 		else:
	# 			try:
	# 				print (" update author ")
	# 				print
	# 				demojson = {
	# 							"id": id,
	# 							"name": name,
	# 							"mail": mail
	# 							# "creation": creation
	# 				}
	# 				jsonresult = ipolservices.demoinfo_update_author(demojson)
	# 				status,error = get_status_and_error_from_json(jsonresult)
	# 				jres['status'] = status
	# 				if error is not None:
	# 						jres['error'] = error
	# 						print jres['error']
	#
	# 				#TODO todos los WS deben devolver status y errors, asi se lo paso directamente al html
	# 			except Exception as e:
	# 				msg = "update author error: %s" % e
	# 				jres['error'] = msg
	# 				logger.error(msg)
	# 				print msg
	#
	# 	else:
	# 		jres['error'] = 'form_valid no ajax'
	# 		logger.warning('DemoinfoSaveAuthorView form_valid no ajax')
	#
	#
	# 	return HttpResponse(json.dumps(jres),content_type='application/json')
	#
	#
	# def form_invalid(self, form):
	#
	# 	jres = dict()
	# 	jres['status'] = 'KO'
	# 	print "invalid form"
	#
	# 	if self.request.is_ajax():
	#
	# 		print " ---invalid ajax form"
	# 		print form.errors
	# 		print form
	#
	# 		#form CON ERORRES, se lo puedo pasar al JS...pero si substituyo el form actual por este..pierdo el submit ajax.
	# 		# form_html = render_crispy_form(form)
	# 		# logger.warning(form_html)
	#
	# 		jres['error'] = str(form.errors)
	# 		jres['status'] = 'KO'
	#
	# 	else:
	# 		jres['error'] = 'form_invalid no ajax'
	# 		logger.warning('form_invalid no ajax')
	#
	# 	return HttpResponse(json.dumps(jres),content_type='application/json')

#editors

class DemoinfoEditorsView(NavbarReusableMixinMF,TemplateView):
	template_name = "demoinfo/demoinfo_editors.html"


	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		# para las pestanas
		self.request.session['topmenu'] = 'topmenu-demoinfo-editors'
		return super(DemoinfoEditorsView, self).dispatch(*args, **kwargs)

	def list_editors(self):
		result = None
		print "list_demos"
		try:
			page_json = ipolservices.demoinfo_demo_list()
			result = DeserializeDemoinfoDemoList(page_json)

		except Exception as e:
			msg=" DemoinfoDemosView Error %s "%e
			logger.error(msg)
			print(msg)

		return result


#
# class DemoinfoGetDDLView(NavbarReusableMixinMF,TemplateView):
#
# 	@method_decorator(login_required)
# 	def dispatch(self, *args, **kwargs):
# 		return super(DemoinfoGetDDLView, self).dispatch(*args, **kwargs)
#
# 	def post(self, request, *args, **kwargs):
# 			context = super(DemoinfoGetDDLView, self).get_context_data(**kwargs)
# 			try:
# 				demo_descp_id = int(self.kwargs['demo_descp_id'])
# 			except ValueError:
# 				msg= "Id is not an integer"
# 				logger.error(msg)
# 				raise ValueError(msg)
#
# 			result= ipolservices.demoinfo_read_demo_description(demo_descp_id)
# 			if result == None:
# 				msg="DemoinfoGetDDLView: Something went wrong using demoinfo WS"
# 				logger.error(msg)
# 				raise ValueError(msg)
#
#
# 			import json
# 			#your_json = '["foo", {"bar":["baz", null, 1.0, 2]}]'
# 			# parsed = json.loads(result)
# 			# result = json.dumps(parsed, indent=4, sort_keys=True)
#
# 			print "result: ",result
# 			return HttpResponse(result,content_type='application/json')
#