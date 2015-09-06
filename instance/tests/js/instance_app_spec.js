// OpenCraft -- tools to aid developing and hosting free software projects
// Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

"use strict";

// Functions //////////////////////////////////////////////////////////////////

// Helpers for testing restangular calls - https://github.com/mgonto/restangular/issues/98

// Apply "sanitizeRestangularOne" function to an array of items
function sanitizeRestangularAll(items) {
    var all = _.map(items, function (item) {
        return sanitizeRestangularOne(item);
    });
    return sanitizeRestangularOne(all);
}

// Remove all Restangular/AngularJS added methods in order to use Jasmine toEqual between the
// retrieved resource and the model
function sanitizeRestangularOne(item) {
    return _.omit(item, "route", "parentResource", "getList", "get", "post", "put", "remove", "head",
                  "trace", "options", "patch", "$get", "$save", "$query", "$remove", "$delete", "$put",
                  "$post", "$head", "$trace", "$options", "$patch", "$then", "$resolved",
                  "restangularCollection", "customOperation", "customGET", "customPOST", "customPUT",
                  "customDELETE", "customGETLIST", "$getList", "$resolved", "restangularCollection",
                  "one", "all", "doGET", "doPOST", "doPUT", "doDELETE", "doGETLIST",
                  "addRestangularMethod", "getRestangularUrl");
}


// Tests //////////////////////////////////////////////////////////////////////

describe('Index', function() {
    beforeEach(function() {
        window.swampdragon = {
            onChannelMessage: sinon.spy(),
            ready: sinon.spy()
        };
    });
    beforeEach(module('InstanceApp'));

    var $controller;

    beforeEach(inject(function(_$controller_){
        // The injector unwraps the underscores (_) from around the parameter names when matching
        $controller = _$controller_;
    }));

    describe('$scope.select', function() {
        var $scope, controller;

        beforeEach(function() {
            $scope = {};
            controller = $controller('Index', { $scope: $scope });
        });

        it('selects the instance', function() {
            $scope.select('a', 'b');
            expect($scope.selected.a).toEqual('b');
        });
    });
});

describe('Instance list', function () {
    var scope, IndexCtrl, httpBackend, instanceList, Restangular;

    beforeEach(angular.mock.module('restangular'));

    describe('Index', function() {
        beforeEach(inject(function($controller, _$httpBackend_, $rootScope, _Restangular_, $state) {
            scope = $rootScope.$new();
            httpBackend = _$httpBackend_;
            Restangular = _Restangular_;

            // Models
            console.log(window.location)
            instanceList = {}; // TODO: Load JSON fixture 'instance/tests/fixtures/api/instances_list.json'
            httpBackend.whenGET('/api/v1/openedxinstance').respond(instanceList);

            IndexCtrl = $controller('Index', {$scope: scope, $state: $state, Restangular: Restangular});
        }));
        afterEach(function () {
            httpBackend.verifyNoOutstandingExpectation();
            httpBackend.verifyNoOutstandingRequest();
        });


        it('should be able to load the instance list from the Django REST API', inject(function ($httpBackend) {
            console.log('OK4');
            // TODO: Why do we need those two?
            var callback = jasmine.createSpy(); // TODO: Chose over sinon.js?
            var success = false;

            console.log('OK4.1');
            var update = scope.updateInstanceList();
            console.log('OK4.2');
            var resolvedUpdate;
            update.then(function(response) {
                console.log('OK4.3');
                resolvedUpdate = response;
            });
            console.log('OK4.4');
            httpBackend.flush();
            console.log('OK5');
            expect(sanitizeRestangularOne(resolvedUpdate)).toEqual(instanceList);
            console.log('OK6');
        }));
    });
    console.log('OK3');
});
