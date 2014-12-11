'''Field classes and related code.'''

import datetime

from lima import abc
from lima import registry
from lima import util


class Field(abc.FieldABC):
    '''Base class for fields.

    Args:
        attr: The optional name of the corresponding attribute.

        get: An optional getter function accepting an object as its only
            parameter and returning the field value.

        val: An optional constant value for the field.

    .. versionadded:: 0.3
        The ``val`` parameter.

    :attr:`attr`, :attr:`get` and :attr:`val` are mutually exclusive.

    When a :class:`Field` object ends up with two or more of the attributes
    :attr:`attr`, :attr:`get` and :attr:`val` regardless (because one or more
    of them are implemented at the class level for example),
    :meth:`lima.schema.Schema.dump` tries to get the field's value in the
    following order: :attr:`val` takes precedence over :attr:`get` and
    :attr:`get` takes precedence over :attr:`attr`.

    If a :class:`Field` object ends up with none of these attributes (not at
    the instance and not at the class level), :meth:`lima.schema.Schema.dump`
    tries to get the field's value by looking for an attribute of the same name
    as the field has within the corresponding :class:`lima.schema.Schema`
    instance.

    '''
    def __init__(self, *, attr=None, get=None, val=None):
        if sum(v is not None for v in (attr, get, val)) > 1:
            raise ValueError('attr, get and val are mutually exclusive.')

        if attr:
            if not isinstance(attr, str) or not str.isidentifier(attr):
                msg = 'attr is not a valid Python identifier: {}'.format(attr)
                raise ValueError(msg)
            self.attr = attr
        elif get:
            if not callable(get):
                raise ValueError('get is not callable.')
            self.get = get
        elif val is not None:
            self.val = val


class Boolean(Field):
    '''A boolean field.

    currently this class has no additional functionality compared to
    :class:`Field`. Nevertheless it should be used over :class:`Field` when
    referencing boolean values as an indicator for a field's type and to keep
    code future-proof.

    '''
    pass


class Float(Field):
    '''A float field.

    currently this class has no additional functionality compared to
    :class:`Field`. Nevertheless it should be used over :class:`Field` when
    referencing float values as an indicator for a field's type and to keep
    code future-proof.

    '''
    pass


class Integer(Field):
    '''An integer field.

    currently this class has no additional functionality compared to
    :class:`Field`. Nevertheless it should be used over :class:`Field` when
    referencing integer values as an indicator for a field's type and to keep
    code future-proof.

    '''
    pass


class String(Field):
    '''A string field.

    currently this class has no additional functionality compared to
    :class:`Field`. Nevertheless it should be used over :class:`Field` when
    referencing string values as an indicator for a field's type and to keep
    code future-proof.

    '''
    pass


class Date(Field):
    '''A date field.

    '''
    @staticmethod
    def pack(val):
        '''Return a string representation of ``val``.

        Args:
            val: The :class:`datetime.date` object to convert.

        Returns:
            The ISO 8601-representation of ``val`` (``YYYY-MM-DD``).
        '''
        return val.isoformat() if val is not None else None


class DateTime(Field):
    '''A DateTime field.

    '''
    @staticmethod
    def pack(val):
        '''Return a string representation of ``val``.

        Args:
            val: The :class:`datetime.datetime` object to convert.

        Returns:
            The ISO 8601-representation of ``val``
            (``YYYY-MM-DD%HH:MM:SS.mmmmmm+HH:MM`` for
            :class:`datetime.datetime` objects with Timezone
            information and microsecond precision).

        '''
        return val.isoformat() if val is not None else None


class _LinkedObjectField(Field):
    '''A field that references the schema of a linked object.

    This is to be considered an abstract class. Concrete implementations will
    have to define their own :meth:`pack` methods, utilizing the associated
    schema of the linked object.

    Args:
        schema: The schema of the linked object. This can be specified via a
            schema *object,* a schema *class* or the qualified *name* of a
            schema class (for when the named schema has not been defined at the
            time of instantiation. If two or more schema classes with the same
            name exist in different modules, the schema class name has to be
            fully module-qualified (see the :ref:`entry on class names
            <on_class_names>` for clarification of these concepts). Schemas
            defined within a local namespace can not be referenced by name.

        attr: The optional name of the corresponding attribute containing the
            linked object(s).

        get: An optional getter function accepting an object as its only
            parameter and returning the field value (the linked object).

        val: An optional constant value for the field (the linked object).

        kwargs: Optional keyword arguments to pass to the :class:`Schema`'s
            constructor when the time has come to instance it. Must be empty if
            ``schema`` is a :class:`lima.schema.Schema` object.

    The schema of the linked object associated with a field of this type will
    be lazily evaluated the first time it is needed. This means that incorrect
    arguments might produce errors at a time after the field's instantiation.

    '''
    def __init__(self, *, schema, attr=None, get=None, val=None, **kwargs):
        super().__init__(attr=attr, get=get, val=val)

        # those will be evaluated later on (in _schema_inst)
        self._schema_arg = schema
        self._schema_kwargs = kwargs

    @util.reify
    def _schema_inst(self):
        '''Determine and return the associated Schema instance (reified).

        If no associated Schema instance exists at call time (because only a
        Schema class name was supplied to the constructor), find the Schema
        class in the global registry and instantiate it.

        Returns:
            A schema instance for the linked object.

        Raises:
            ValueError: If ``kwargs`` were specified to the field constructor
                even if a :class:`lima.schema.Schema` *instance* was provided
                as the ``schema`` arg.

            TypeError: If the ``schema`` arg provided to the field constructor
                has the wrong type.

        '''
        with util.complain_about('Lazy evaluation of schema instance'):

            # those were supplied to field constructor
            schema = self._schema_arg
            kwargs = self._schema_kwargs

            # in case schema is a Schema object
            if isinstance(schema, abc.SchemaABC):
                if kwargs:
                    msg = ('No additional keyword args must be '
                           'supplied to field constructor if '
                           'schema already is a Schema object.')
                    raise ValueError(msg)
                return schema

            # in case schema is a schema class
            elif (isinstance(schema, type) and
                  issubclass(schema, abc.SchemaABC)):
                return schema(**kwargs)

            # in case schema is a string
            elif isinstance(schema, str):
                cls = registry.global_registry.get(schema)
                return cls(**kwargs)

            # otherwise fail
            msg = 'schema arg supplied to constructor has illegal type ({})'
            raise TypeError(msg.format(type(schema)))

    def pack(self, val):
        raise NotImplementedError


class Embed(_LinkedObjectField):
    '''A Field to embed linked object(s).

    Args:
        schema: The schema of the linked object. This can be specified via a
            schema *object,* a schema *class* or the qualified *name* of a
            schema class (for when the named schema has not been defined at the
            time of instantiation. If two or more schema classes with the same
            name exist in different modules, the schema class name has to be
            fully module-qualified (see the :ref:`entry on class names
            <on_class_names>` for clarification of these concepts). Schemas
            defined within a local namespace can not be referenced by name.

        attr: The optional name of the corresponding attribute containing the
            linked object(s).

        get: An optional getter function accepting an object as its only
            parameter and returning the field value (the linked object).

        val: An optional constant value for the field (the linked object).

        kwargs: Optional keyword arguments to pass to the :class:`Schema`'s
            constructor when the time has come to instance it. Must be empty if
            ``schema`` is a :class:`lima.schema.Schema` object.

    The schema of the linked object associated with a field of this type will
    be lazily evaluated the first time it is needed. This means that incorrect
    arguments might produce errors at a time after the field's instantiation.

    Examples: ::

        # refer to PersonSchema class
        author = Embed(schema=PersonSchema)

        # refer to PersonSchema class with additional params
        artists = Embed(schema=PersonSchema, exclude='email', many=True)

        # refer to PersonSchema object
        author = Embed(schema=PersonSchema())

        # refer to PersonSchema object with additional params
        # (note that Embed() itself gets no kwargs)
        artists = Embed(schema=PersonSchema(exclude='email', many=true))

        # refer to PersonSchema per name
        author = Embed(schema='PersonSchema')

        # refer to PersonSchema per name with additional params
        author = Embed(schema='PersonSchema', exclude='email', many=True)

        # refer to PersonSchema per module-qualified name
        # (in case of ambiguity)
        author = Embed(schema='project.persons.PersonSchema')

        # specify attr name as well
        user = Embed(attr='login_user', schema=PersonSchema)

    '''
    def pack(self, val):
        '''Return the output of the linked object's schema's dump method.

        Args:
            val: The nested object to convert.

        Returns:
            The output of the linked :class:`lima.schema.Schema`'s
            :meth:`lima.schema.Schema.dump` method (or None if ``val`` is
            None).

        '''
        return self._schema_inst.dump(val) if val is not None else None


class Reference(_LinkedObjectField):
    '''A Field to reference linked object(s).

    Constructor arguments are similar to those of :class:`Embed`.

    '''
    def pack(self, val):
        raise NotImplementedError


Nested = Embed
'''A Field to embed linked object(s)

:class:`Nested` is the old name of class :class:`Embed`.

.. deprecated:: 0.4
    Will be removed in 0.5. Use :class:`Embed` instead'''


TYPE_MAPPING = {
    bool: Boolean,
    float: Float,
    int: Integer,
    str: String,
    datetime.date: Date,
    datetime.datetime: DateTime,
}
'''A mapping of native Python types to :class:`Field` classes.

This can be used to automatically create fields for objects you know the
attribute's types of.'''
