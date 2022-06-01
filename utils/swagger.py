from collections import defaultdict

from drf_yasg.generators import OpenAPISchemaGenerator, EndpointEnumerator


class ScribbleOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_endpoints(self, request):
        enumerator = self.endpoint_enumerator_class(self._gen.patterns, self._gen.urlconf, request=request)
        endpoints = enumerator.get_api_endpoints()

        view_paths = defaultdict(list)
        view_cls = {}

        for path, method, callback in endpoints:
            http_method_names = callback.view_initkwargs.get('http_method_names')
            if http_method_names and method.lower() != http_method_names[0]:
                continue

            view = self.create_view(callback, method, request)
            path = self.coerce_path(path, view)
            view_paths[path].append((method, view))
            view_cls[path] = callback.cls

        return {path: (view_cls[path], methods) for path, methods in view_paths.items()}
