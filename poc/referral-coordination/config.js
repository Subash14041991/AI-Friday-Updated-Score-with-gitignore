// Scenario vocabulary lives here; the workflow engine is domain-neutral.
window.WorkspaceConfig = {
  title: 'Referral coordination',
  subtitle: 'Track referrals, resolve missing information, and record hand-offs.',
  itemLabel: 'Referral',
  searchHint: 'ID, specialty, or provider',
  receiptNextAction: 'Follow the next agreed care step. Receipt is not completed care.',
  noteHelp: 'Record administrative coordination details only; do not include patient-identifying or clinical information.',
  footer: 'Clinical records remain in their source systems. A recorded receipt is not clinical acceptance or completed care.',
  storageKey: 'referral-coordination-v1',
  coordinator: 'Care coordinator',
  followUpMinutes: 30,
  fields: [
    {key:'specialty', label:'Specialty'},
    {key:'receiver', label:'Receiving provider'}
  ],
  examples: [
    {id:'EXAMPLE-001', specialty:'Cardiology', receiver:'Example provider A'},
    {id:'EXAMPLE-002', specialty:'', receiver:'Example provider B'},
    {id:'EXAMPLE-003', specialty:'Orthopedics', receiver:''}
  ]
};
