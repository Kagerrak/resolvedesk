# ResolveDesk glossary

Domain language for a support operation that drafts grounded replies under human control.

## People and access

**Workspace**: An isolated support operation belonging to one business. Its tickets, knowledge and handling history belong to that operation alone.

**Member**: A person authorized to access a particular Workspace under an assigned role.
_Avoid_: Customer, account

**Admin**: A Member who manages Workspace membership, knowledge and connections, and may handle tickets.

**Agent**: A Member who handles tickets, reviews drafts and approves permitted support actions.

**Viewer**: A Member who can inspect permitted Workspace information without changing it.

**Customer**: A person seeking assistance through email, distinct from a Workspace Member.
_Avoid_: User, member

## Inbox and assistance

**Ticket**: A support case containing a conversation and its handling history. Its state is open, pending or resolved; assignment and priority are separate attributes.

**Message**: An immutable customer or agent contribution to a Ticket conversation. A Draft revision is not a Message.

**Draft reply**: A proposed customer response that has not been delivered.

**Draft revision**: A particular saved wording of a Draft reply together with its supporting evidence and Proposed actions.

**Proposed action**: A suggested internal Ticket assignment, status, priority or tag change awaiting explicit authorization.

**Approval**: A Member's explicit authorization of an exact Draft revision and Proposed actions against the reviewed conversation and published knowledge. A changed basis makes the authorization stale.

**Delivery attempt**: A recorded effort to deliver an approved reply. Its outcome can be confirmed, failed or uncertain; authorization alone does not establish delivery.

**Escalation**: A request for human judgment when available evidence or authority is insufficient.

## Knowledge

**Knowledge document**: A curated source of support information belonging to a Workspace. A document is usable as answer evidence only through a published Document version.

**Document version**: A particular revision of a Knowledge document, preserving the source identity and passage locations of that revision.
_Avoid_: Knowledge overwrite

**Published snapshot**: The set of published Document versions available as support evidence at a particular point in time.

**Citation**: A reference to a specific passage of a Document version offered in support of a statement. The reference alone does not establish that the statement is supported.

**Retrieval run**: A saved search of a Ticket conversation against published Workspace knowledge, recording the query, ranking method and source-version passage references. Fixture runs do not establish AI quality.

**Generation run**: A recorded attempt to prepare a Draft reply using a Ticket and its selected supporting knowledge. It preserves what informed the attempt and whether it succeeded. It does not authorize delivery or other Ticket actions.

## Operations

**Connector**: A Workspace's authorized connection to an external communication service.

**Audit event**: A record of a meaningful support action and who or what performed it.


## Quality assessment

**Evaluation dataset**: A versioned collection of authored support scenarios, knowledge and expected outcomes used to assess retrieval and reply assistance. Synthetic labels are not independent human ground truth.

**Evaluation case**: One support scenario and its stated expectations within an Evaluation dataset.

**Evaluation run**: A recorded assessment of Evaluation cases against a particular knowledge basis and assistance configuration. Its results describe the observed set rather than universal quality or safety.
