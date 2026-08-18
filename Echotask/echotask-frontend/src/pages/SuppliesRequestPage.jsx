import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  createSupplyRequest,
  getSupplyItems,
  getSupplyRequests,
  updateSupplyRequestStatus,
} from '../api/supplies'
import SearchBar from "../components/SearchBar";
import CategoryAccordion from "../components/CategoryAccordion";
import SupplyItemRow from "../components/SupplyItemRow";

function SuppliesRequestPage({ user }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [supplyItems, setSupplyItems] = useState([]);
  const [selectedItems, setSelectedItems] = useState({});
  const [isLoading, setIsLoading] = useState(user.role === 'worker');
  const [loadError, setLoadError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const loadSupplyItems = useCallback(async () => {
    if (user.role !== 'worker') return;

    setIsLoading(true);
    setLoadError('');
    try {
      setSupplyItems(await getSupplyItems());
    } catch (requestError) {
      setLoadError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }, [user.role]);

  useEffect(() => {
    loadSupplyItems();
  }, [loadSupplyItems]);

  const handleQuantityChange = (itemId, quantity) => {
    setSubmitError('');
    setSuccessMessage('');
    setSelectedItems((prev) => ({
      ...prev,
      [itemId]: quantity,
    }));
  };

  const suppliesByCategory = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    const groupedItems = {};
    supplyItems.forEach((item) => {
      if (normalizedSearch && !item.item_name.toLowerCase().includes(normalizedSearch)) return;
      if (!groupedItems[item.category]) groupedItems[item.category] = [];
      groupedItems[item.category].push(item);
    });
    return Object.entries(groupedItems).sort(([firstCategory], [secondCategory]) =>
      firstCategory.localeCompare(secondCategory),
    );
  }, [searchTerm, supplyItems]);

  const requestItems = supplyItems
    .map((item) => ({
      item_id: item.item_id,
      item_name: item.item_name,
      quantity: selectedItems[item.item_id] || 0,
    }))
    .filter((item) => Number.isInteger(item.quantity) && item.quantity > 0);

  async function handleSubmit() {
    if (!user.area_id) {
      setSubmitError('Supply requests are unavailable because your account has no regular area.');
      return;
    }
    if (requestItems.length === 0) {
      setSubmitError('Choose at least one supply item before submitting.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError('');
    setSuccessMessage('');
    try {
      const result = await createSupplyRequest({
        area_id: user.area_id,
        items: requestItems.map(({ item_id, quantity }) => ({ item_id, quantity })),
      });
      setSelectedItems({});
      setSuccessMessage(`${result.message}. Request #${result.supply_request_id}.`);
    } catch (requestError) {
      setSubmitError(requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (user.role !== 'worker') return <SupplyRequestReview user={user} />;

  return (
    <div className="app-container" style={{ color: "white" }}>
      <header>
        <h1>Supplies Request Sheet</h1>
      </header>

      <div
        style={{
          backgroundColor: "#1e1e1e",
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "20px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        }}
      >
        {isLoading && <p className="muted-text" aria-live="polite">Loading supply catalog&hellip;</p>}
        {!isLoading && loadError && (
          <div className="attendance-error" role="alert">
            <p className="form-error">{loadError}</p>
            <button type="button" className="secondary-button" onClick={loadSupplyItems}>Try again</button>
          </div>
        )}
        {!isLoading && !loadError && supplyItems.length === 0 && (
          <p className="empty-state">No supply items are available.</p>
        )}
        {!isLoading && !loadError && supplyItems.length > 0 && (
          <>
            <SearchBar searchTerm={searchTerm} onSearchChange={setSearchTerm} />
            {suppliesByCategory.length === 0 && (
              <p className="empty-state">No supply items match your search.</p>
            )}
            {suppliesByCategory.map(([category, items]) => (
            <CategoryAccordion
              key={category}
              label={category}
            >
              {items.map((item) => (
                <SupplyItemRow
                  key={item.item_id}
                  itemId={item.item_id}
                  itemName={item.item_name}
                  quantity={selectedItems[item.item_id] || 0}
                  onQuantityChange={handleQuantityChange}
                  disabled={isSubmitting}
                />
              ))}
            </CategoryAccordion>
            ))}
          </>
        )}
      </div>

      {/* Summary */}
      <div
        style={{
          backgroundColor: "#2c2c2c",
          padding: "15px",
          borderRadius: "10px",
          marginBottom: "20px",
        }}
      >
        <h3>Summary</h3>
        {requestItems.length === 0 ? (
          <p>No items selected yet.</p>
        ) : (
          <ul>
            {requestItems.map((item) => (
                <li key={item.item_id}>
                  {item.item_name}: {item.quantity}
                </li>
            ))}
          </ul>
        )}
      </div>

      {submitError && <p className="form-error" role="alert">{submitError}</p>}
      {successMessage && <p className="form-success" aria-live="polite">{successMessage}</p>}
      <button
        onClick={handleSubmit}
        disabled={isLoading || Boolean(loadError) || supplyItems.length === 0 || isSubmitting}
        style={{
          backgroundColor: "#4caf50",
          color: "white",
          padding: "12px 24px",
          fontSize: "16px",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
        }}
      >
        {isSubmitting ? 'Submitting...' : 'Submit Request'}
      </button>
    </div>
  );
}

function SupplyRequestReview({ user }) {
  const [requests, setRequests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [updatingRequestId, setUpdatingRequestId] = useState(null);
  const [updateError, setUpdateError] = useState('');

  const loadRequests = useCallback(async () => {
    setIsLoading(true);
    setLoadError('');
    try {
      setRequests(await getSupplyRequests());
    } catch (requestError) {
      setLoadError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  async function handleStatusChange(requestId, status) {
    setUpdatingRequestId(requestId);
    setUpdateError('');
    try {
      await updateSupplyRequestStatus(requestId, status);
      await loadRequests();
    } catch (requestError) {
      setUpdateError(requestError.message);
    } finally {
      setUpdatingRequestId(null);
    }
  }

  return (
    <section>
      <div className="page-heading">
        <p className="eyebrow">Operations</p>
        <h2>Supply requests</h2>
        <p className="muted-text">Review requests submitted by workers across all areas.</p>
      </div>
      {updateError && <p className="form-error" role="alert">{updateError}</p>}
      {isLoading && <p className="muted-text" aria-live="polite">Loading supply requests&hellip;</p>}
      {!isLoading && loadError && (
        <div className="attendance-error" role="alert">
          <p className="form-error">{loadError}</p>
          <button type="button" className="secondary-button" onClick={loadRequests}>Try again</button>
        </div>
      )}
      {!isLoading && !loadError && requests.length === 0 && (
        <p className="empty-state">No supply requests have been submitted.</p>
      )}
      {!isLoading && !loadError && requests.length > 0 && (
        <ul className="supply-request-list">
          {requests.map((request) => (
            <li key={request.supply_request_id} className="supply-request-row">
              <div className="supply-request-heading">
                <div>
                  <span className="supply-request-number">Request #{request.supply_request_id}</span>
                  <h3>{request.submitted_by_name || 'Unknown worker'}</h3>
                  <p>{request.area_name || 'Unknown area'}</p>
                </div>
                <div className="supply-request-status">
                  <span className={`status-badge${request.status === 'Completed' ? '' : ' status-badge--pending'}`}>
                    {request.status}
                  </span>
                  {user.role === 'supervisor' && (
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={updatingRequestId !== null}
                      onClick={() => handleStatusChange(
                        request.supply_request_id,
                        request.status === 'Completed' ? 'Submitted' : 'Completed',
                      )}
                    >
                      {updatingRequestId === request.supply_request_id
                        ? 'Updating...'
                        : request.status === 'Completed' ? 'Reopen' : 'Mark completed'}
                    </button>
                  )}
                </div>
              </div>
              <ul className="supply-request-items">
                {request.items.map((item) => (
                  <li key={item.item_id}>
                    <span>{item.item_name || 'Unknown item'}</span>
                    <strong>&times; {item.quantity}</strong>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default SuppliesRequestPage;
